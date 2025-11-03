# 自动替换注册表脚本 - 隐藏窗口版
# 功能：搜索所有包含"C:\Users\Administrator"的注册表项，替换为当前用户名路径

# 获取当前用户名
$currentUser = $env:USERNAME
$currentUserProfile = "C:\Users\$currentUser"

# 定义要搜索和替换的模式（不区分大小写）
$searchPatterns = @(
    "C:\\Users\\Administrator",
    "C:\\Users\\administrator",
    "C:\\Users\\ADMINISTRATOR"
)

# 全局统计变量和控制标志
$global:SearchedCount = 0
$global:FoundCount = 0
$global:ModifiedCount = 0
$global:ErrorCount = 0
$global:StartTime = Get-Date
$global:LastFoundTime = Get-Date
$global:LastProgressTime = Get-Date
$global:ShouldContinue = $true

# 设置搜索参数
$maxSearchCount = 50000  # 增加到50000
$timeoutSeconds = 20     # 增加到20秒
$progressIntervalSeconds = 2

# 创建日志文件
$logPath = "C:\Windows\Temp\reg_replace.log"
"开始注册表路径替换 - $(Get-Date)" | Out-File -FilePath $logPath -Encoding UTF8
"当前用户: $currentUser" | Out-File -FilePath $logPath -Append -Encoding UTF8
"替换目标: $currentUserProfile" | Out-File -FilePath $logPath -Append -Encoding UTF8
"最大搜索数量: $maxSearchCount" | Out-File -FilePath $logPath -Append -Encoding UTF8
"超时时间: $timeoutSeconds 秒" | Out-File -FilePath $logPath -Append -Encoding UTF8
"进程ID: $PID" | Out-File -FilePath $logPath -Append -Encoding UTF8
"用户上下文: $([Security.Principal.WindowsIdentity]::GetCurrent().Name)" | Out-File -FilePath $logPath -Append -Encoding UTF8
"" | Out-File -FilePath $logPath -Append -Encoding UTF8

# 检查管理员权限
function Test-Administrator {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 检查是否应该继续搜索
function Test-ShouldContinue {
    # 检查全局停止标志
    if (-not $global:ShouldContinue) {
        return $false
    }

    # 检查是否达到最大搜索数量
    if ($global:SearchedCount -ge $maxSearchCount) {
        Write-Output "已达到最大搜索数量 $maxSearchCount"
        $global:ShouldContinue = $false
        return $false
    }

    # 检查是否超时（30秒内没有找到新条目）
    # 只有当已经找到至少一个匹配项时才启用超时检查
    if ($global:FoundCount -gt 0) {
        $timeSinceLastFound = (Get-Date) - $global:LastFoundTime
        if ($timeSinceLastFound.TotalSeconds -gt $timeoutSeconds) {
            Write-Output "已超过 $timeoutSeconds 秒未找到新条目，搜索完成"
            $global:ShouldContinue = $false
            return $false
        }
    }

    return $true
}

# 显示进度信息
function Show-Progress {
    param([string]$path)

    $timeSinceLastProgress = (Get-Date) - $global:LastProgressTime
    if ($timeSinceLastProgress.TotalSeconds -ge $progressIntervalSeconds) {
        $progressPercent = [math]::Round(($global:SearchedCount / $maxSearchCount) * 100, 1)
        Write-Output "已搜索 $($global:SearchedCount) 个注册表值，找到 $($global:FoundCount) 个匹配项，已替换 $($global:ModifiedCount) 个 ($progressPercent%)"
        Write-Output "当前搜索路径: $path"
        $global:LastProgressTime = Get-Date
    }
}

# 优化后的递归搜索函数
function Search-And-Replace-Registry {
    param(
        [string]$path
    )

    # 检查是否应该继续
    if (-not (Test-ShouldContinue)) {
        return
    }

    try {
        # 获取当前注册表项
        $item = Get-Item -Path $path -ErrorAction SilentlyContinue
        if (-not $item) {
            return
        }

        # 处理当前项的所有值
        $valueNames = $item.GetValueNames()
        foreach ($valueName in $valueNames) {
            # 检查是否应该继续
            if (-not (Test-ShouldContinue)) {
                return
            }

            try {
                $global:SearchedCount++

                # 显示进度信息
                Show-Progress -path $path

                # 获取值的数据和类型
                $value = $item.GetValue($valueName, $null, "DoNotExpandEnvironmentNames")
                $valueKind = $item.GetValueKind($valueName)

                # 只处理字符串类型的值
                if (($valueKind -eq "String" -or $valueKind -eq "ExpandString") -and $value -is [string] -and $value.Length -gt 0) {
                    $originalValue = $value
                    $modifiedValue = $originalValue
                    $wasModified = $false

                    # 对每个搜索模式进行检查和替换
                    foreach ($pattern in $searchPatterns) {
                        # 使用正则表达式进行不区分大小写的匹配和替换
                        if ($modifiedValue -imatch $pattern) {
                            # 替换为当前用户路径（区分大小写）
                            $modifiedValue = $modifiedValue -ireplace $pattern, $currentUserProfile
                            $wasModified = $true
                        }
                    }

                    # 如果值被修改，则写回注册表
                    if ($wasModified) {
                        try {
                            Set-ItemProperty -Path $path -Name $valueName -Value $modifiedValue -Force -ErrorAction Stop

                            Write-Output "成功替换: $path\$valueName"
                            Write-Output "原值: $originalValue"
                            Write-Output "新值: $modifiedValue"

                            "成功替换: $path\$valueName" | Out-File -FilePath $logPath -Append -Encoding UTF8
                            "原值: $originalValue" | Out-File -FilePath $logPath -Append -Encoding UTF8
                            "新值: $modifiedValue" | Out-File -FilePath $logPath -Append -Encoding UTF8
                            "" | Out-File -FilePath $logPath -Append -Encoding UTF8

                            $global:ModifiedCount++
                            $global:FoundCount++
                            $global:LastFoundTime = Get-Date
                        } catch {
                            $global:ErrorCount++
                            Write-Output "设置注册表值失败: $path\$valueName - $($_.Exception.Message)"
                            "设置注册表值失败: $path\$valueName - $($_.Exception.Message)" | Out-File -FilePath $logPath -Append -Encoding UTF8
                        }
                    }
                }
            } catch {
                $global:ErrorCount++
                Write-Output "处理注册表值失败: $path\$valueName - $($_.Exception.Message)"
                "处理注册表值失败: $path\$valueName - $($_.Exception.Message)" | Out-File -FilePath $logPath -Append -Encoding UTF8
            }
        }

        # 递归处理所有子项 - 使用更高效的递归方式
        try {
            $subKeys = Get-ChildItem -Path $path -ErrorAction SilentlyContinue
            foreach ($subKey in $subKeys) {
                # 检查是否应该继续
                if (-not (Test-ShouldContinue)) {
                    return
                }
                Search-And-Replace-Registry -path $subKey.PSPath
            }
        } catch {
            # 忽略子项访问错误，继续处理其他项
        }
    } catch {
        $global:ErrorCount++
        Write-Output "访问注册表路径失败: $path - $($_.Exception.Message)"
        "访问注册表路径失败: $path - $($_.Exception.Message)" | Out-File -FilePath $logPath -Append -Encoding UTF8
    }
}

# 主执行逻辑
try {
    Write-Output "开始注册表路径替换..."
    Write-Output "当前用户: $currentUser"
    Write-Output "替换目标: $currentUserProfile"
    Write-Output "最大搜索数量: $maxSearchCount"
    Write-Output "超时时间: $timeoutSeconds 秒"
    Write-Output "日志文件: $logPath"

    # 检查管理员权限
    if (-not (Test-Administrator)) {
        Write-Output "警告: 当前未以管理员权限运行，可能无法访问所有注册表路径"
        "警告: 当前未以管理员权限运行" | Out-File -FilePath $logPath -Append -Encoding UTF8
    } else {
        Write-Output "当前以管理员权限运行"
        "当前以管理员权限运行" | Out-File -FilePath $logPath -Append -Encoding UTF8
    }

    # 定义要搜索的注册表根路径（完整范围）
    $registryRoots = @(
        "HKEY_CURRENT_USER",
        "HKEY_LOCAL_MACHINE\SOFTWARE",
        "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control",
        "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services",
        "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum",
        "HKEY_CLASSES_ROOT",
        "HKEY_USERS"
    )

    # 处理每个注册表根路径
    foreach ($registryRoot in $registryRoots) {
        # 检查是否应该继续
        if (-not (Test-ShouldContinue)) {
            break
        }

        $registryPath = "Registry::$registryRoot"
        if (Test-Path $registryPath) {
            Write-Output "正在搜索: $registryRoot"
            "开始搜索: $registryRoot" | Out-File -FilePath $logPath -Append -Encoding UTF8
            Search-And-Replace-Registry -path $registryPath
            "完成搜索: $registryRoot" | Out-File -FilePath $logPath -Append -Encoding UTF8
        } else {
            Write-Output "路径不存在: $registryRoot"
            "路径不存在: $registryRoot" | Out-File -FilePath $logPath -Append -Encoding UTF8
        }
    }

    # 计算总耗时
    $totalTime = (Get-Date) - $global:StartTime

    # 输出最终结果
    Write-Output "=== 替换操作完成 ==="
    Write-Output "总搜索时间: $([math]::Round($totalTime.TotalMinutes, 2)) 分钟"
    Write-Output "已搜索注册表值: $($global:SearchedCount)"
    Write-Output "找到匹配项: $($global:FoundCount)"
    Write-Output "成功替换: $($global:ModifiedCount)"
    Write-Output "遇到错误: $($global:ErrorCount)"

    # 记录最终结果到日志
    "=== 替换操作完成 ===" | Out-File -FilePath $logPath -Append -Encoding UTF8
    "总搜索时间: $([math]::Round($totalTime.TotalMinutes, 2)) 分钟" | Out-File -FilePath $logPath -Append -Encoding UTF8
    "已搜索注册表值: $($global:SearchedCount)" | Out-File -FilePath $logPath -Append -Encoding UTF8
    "找到匹配项: $($global:FoundCount)" | Out-File -FilePath $logPath -Append -Encoding UTF8
    "成功替换: $($global:ModifiedCount)" | Out-File -FilePath $logPath -Append -Encoding UTF8
    "遇到错误: $($global:ErrorCount)" | Out-File -FilePath $logPath -Append -Encoding UTF8

    # 提示可能需要重启
    if ($global:ModifiedCount -gt 0) {
        Write-Output "注意: 部分更改可能需要重启系统或应用程序才能生效"
        "注意: 部分更改可能需要重启系统或应用程序才能生效" | Out-File -FilePath $logPath -Append -Encoding UTF8
    }

} catch {
    Write-Output "执行过程中发生严重错误: $($_.Exception.Message)"
    "执行过程中发生严重错误: $($_.Exception.Message)" | Out-File -FilePath $logPath -Append -Encoding UTF8
}

exit 0
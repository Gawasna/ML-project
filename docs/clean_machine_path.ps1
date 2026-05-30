# System Machine PATH Cleanup Script (Requires Administrator Privileges)
# Run this script from an elevated PowerShell console to clean and optimize the system-wide PATH variable,
# resolving potential issues caused by PATH overflow (over 2048 characters).

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "This script MUST be run with Administrator privileges!"
    Write-Warning "Please open PowerShell as Administrator (right-click -> 'Run as Administrator') and execute this script."
    Exit
}

# 1. Read the current Machine PATH from Registry (without expansion)
$registryKey = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey("System\CurrentControlSet\Control\Session Manager\Environment", $true)
$machinePath = $registryKey.GetValue("PATH", "", [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)

Write-Output "--- Starting Machine PATH cleanup ---"
Write-Output "Current Machine PATH length: $($machinePath.Length) characters"

# 2. Split and filter directories
$parts = $machinePath -split ';'
$cleanParts = @()
$removedInvalid = @()
$removedDuplicates = @()

foreach ($p in $parts) {
    if ([string]::IsNullOrEmpty($p)) { continue }
    $pClean = $p.Trim()
    
    # Check for duplicates (case-insensitive)
    if ($cleanParts | Where-Object { $_.ToLower() -eq $pClean.ToLower() }) {
        $removedDuplicates += $pClean
        continue
    }
    
    # Verify if path exists on disk
    if (Test-Path -Path $pClean -ErrorAction SilentlyContinue) {
        $cleanParts += $pClean
    } else {
        $removedInvalid += $pClean
    }
}

# 3. Combine and write back
$newMachinePath = [string]::Join(";", $cleanParts)

Write-Output ""
Write-Output "=== CLEANUP RESULTS ==="
Write-Output "Removed $($removedDuplicates.Count) duplicate entries."
foreach ($d in $removedDuplicates) { Write-Output "  - $d" }

Write-Output "Removed $($removedInvalid.Count) non-existent (garbage) entries."
foreach ($i in $removedInvalid) { Write-Output "  - $i" }

# Write to Registry using ExpandString to preserve expandable variables like %SystemRoot%
$registryKey.SetValue("PATH", $newMachinePath, [Microsoft.Win32.RegistryValueKind]::ExpandString)
$registryKey.Close()

Write-Output ""
Write-Output "Successfully updated Machine PATH!"
Write-Output "New Machine PATH length: $($newMachinePath.Length) characters"
Write-Output "Saved: $($machinePath.Length - $newMachinePath.Length) characters"

# 4. Broadcast changes
try {
    $signature = '[DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, IntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out IntPtr lpdwResult);'
    $type = Add-Type -MemberDefinition $signature -Name "Win32Utils" -Namespace "Win32" -PassThru
    $result = [IntPtr]::Zero
    $type::SendMessageTimeout([IntPtr]0xffff, 0x001a, [IntPtr]::Zero, "Environment", 2, 5000, [ref]$result)
    Write-Output "Broadcasted Environment update signal to Windows."
} catch {
    Write-Warning "Could not broadcast environment change: $_"
}

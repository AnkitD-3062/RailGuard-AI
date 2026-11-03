param(
    [string]$Destination = "datasets/crowdhuman_raw"
)

$ErrorActionPreference = "Stop"
$files = @(
    @{ Name = "CrowdHuman_train01.zip"; Sha256 = "7ba340163cff0f2446027af95dc96bcb9c66be18506eabb57822c400a7efd3b8" },
    @{ Name = "CrowdHuman_train02.zip"; Sha256 = "d9ecfb43eaf8381ddd4d1ff4e9a0877b694dbfba7a7a33ed3966ee2c2a628663" },
    @{ Name = "CrowdHuman_train03.zip"; Sha256 = "9cac171914c4f5c7371e3d42d20b50858caa1602811ae573aa35bbfe672dc29f" },
    @{ Name = "CrowdHuman_val.zip"; Sha256 = "c0ab99bb80ac162cd3efdf94a1a6100c4f059a61d69596412c6b44ebc20d1363" },
    @{ Name = "annotation_train.odgt"; Sha256 = "6bf241a79f19e30cf52681eab3392368bd5a534164be9272e7a808cb284d9f77" },
    @{ Name = "annotation_val.odgt"; Sha256 = "be422c79a190ff7e30fe5cbd74cbf45a2dadda6c5af58c6ec11a038ba2993c04" }
)

New-Item -ItemType Directory -Path $Destination -Force | Out-Null
foreach ($file in $files) {
    $target = Join-Path $Destination $file.Name
    if (-not (Test-Path $target)) {
        $url = "https://huggingface.co/datasets/sshao0516/CrowdHuman/resolve/main/$($file.Name)"
        Write-Host "Downloading $($file.Name) ..."
        curl.exe -L --fail --retry 3 --continue-at - -o $target $url
    }
    $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $file.Sha256) {
        throw "Checksum failed for $($file.Name). Delete it and run this script again."
    }
}

Get-ChildItem "$Destination\*.zip" | ForEach-Object {
    Write-Host "Extracting $($_.Name) ..."
    Expand-Archive -LiteralPath $_.FullName -DestinationPath "$Destination\images" -Force
}
Write-Host "CrowdHuman download and extraction complete." -ForegroundColor Green

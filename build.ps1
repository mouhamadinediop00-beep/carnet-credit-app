# Compile des APK signes (un par architecture) et prepare les fichiers a publier.
# Usage : .\build.ps1   (depuis la racine du projet)
$ErrorActionPreference = "Stop"

$mdp = Read-Host "Mot de passe du keystore" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($mdp)
$clair = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)

$env:FLET_ANDROID_SIGNING_KEY_STORE_PASSWORD = $clair
$env:FLET_ANDROID_SIGNING_KEY_PASSWORD = $clair

try {
    if (Test-Path "build\apk") { Remove-Item -Recurse -Force "build\apk" }

    flet build apk --split-per-abi `
        --android-signing-key-store "$env:USERPROFILE\cles\carnet-credit.jks" `
        --android-signing-key-alias carnet

    if ($LASTEXITCODE -ne 0) { throw "La compilation a echoue." }
}
finally {
    Remove-Item Env:FLET_ANDROID_SIGNING_KEY_STORE_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:FLET_ANDROID_SIGNING_KEY_PASSWORD -ErrorAction SilentlyContinue
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
}

# --- Preparation des fichiers a publier ---
New-Item -ItemType Directory -Force "release" | Out-Null
Remove-Item "release\*.apk" -ErrorAction SilentlyContinue

$apks = Get-ChildItem "build\apk" -Filter *.apk
Write-Host ""
Write-Host "Fichiers produits par Flet :"
$apks | ForEach-Object { Write-Host ("  {0}  ({1:N1} Mo)" -f $_.Name, ($_.Length / 1MB)) }

$arm64 = $apks | Where-Object { $_.Name -match "arm64" } | Select-Object -First 1
$armv7 = $apks | Where-Object { $_.Name -match "armeabi|v7a|armv7" } | Select-Object -First 1

if ($arm64) { Copy-Item $arm64.FullName "release\carnet-credit-arm64.apk" }
if ($armv7) { Copy-Item $armv7.FullName "release\carnet-credit-armv7.apk" }

Write-Host ""
if (-not $arm64 -and -not $armv7) {
    Write-Warning "Aucun APK arm64 ou armv7 reconnu. Regardez les noms ci-dessus (dir build\apk)."
}
else {
    Write-Host "A publier sur GitHub (dossier release) :"
    Get-ChildItem "release" -Filter *.apk | ForEach-Object {
        Write-Host ("  {0}  ({1:N1} Mo)" -f $_.Name, ($_.Length / 1MB))
    }
}

if ($PSVersionTable.PSVersion.Major -lt 3) {
	Write-Error "Yêu cầu PowerShell 3.0 trở lên. Vui lòng nâng cấp PowerShell."
	exit 1
}

python -m venv venv

# Kích hoạt (PowerShell)
if (Test-Path .\venv\Scripts\Activate.ps1) {
	. .\venv\Scripts\Activate.ps1
} else {
	Write-Error "Không tìm thấy .\venv\Scripts\Activate.ps1. Kiểm tra việc tạo venv hoặc đường dẫn Python."
	exit 1
}

if (-not $env:VIRTUAL_ENV -or -not (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe")) {
	if (Test-Path .\venv\Scripts\Activate.ps1) {
		. .\venv\Scripts\Activate.ps1
	} else {
		Write-Error "Không thể kích hoạt lại môi trường ảo .\venv."
		exit 1
	}
}

if (Test-Path .\requirements.txt) {
	pip install -r .\requirements.txt
} else {
	Write-Error "Không tìm thấy file requirements.txt trong thư mục hiện tại."
	exit 1
}

if (Test-Path .\scripts\setup_binaries.py) {
	python .\scripts\setup_binaries.py
	if ($LASTEXITCODE -ne 0) {
		Write-Error "Chạy scripts/setup_binaries.py thất bại."
		exit 1
	}
} else {
	Write-Error "Không tìm thấy file .\scripts\setup_binaries.py trong thư mục hiện tại."
	exit 1
}


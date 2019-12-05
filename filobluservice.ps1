#!/usr/bin/env pwsh

# $args[0] = stop

$path_to_filoblu_service_file = "C:\\Users\\UserName\\FiloBlu"

function Test-Administrator
{
  [OutputType([bool])]
  param()
  process {
    [Security.Principal.WindowsPrincipal]$user = [Security.Principal.WindowsIdentity]::GetCurrent();
    return $user.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator);
  }
}

if (-not (Test-Administrator))
{
  Write-Verbose "This script must be executed as Administrator." -ForegroundColor Red
  exit 1;
}
else
{
  $service = Get-Service -Name FiloBluService 2> $null
  #$service = Get-WmiObject win32_service | ?{$_.Name -like '*FiloBluService*'} | select PathName, State
  #$service_path = $service.PathName

  if ( -not $service )
  {
    Write-Verbose "The Service is not installed. Automatically installed and started" -ForegroundColor Green
    Push-Location > $null
    Set-Location $path_to_filoblu_service_file
    New-Item -Path ..\logs -ItemType directory -Force -ErrorAction SilentlyContinue > $null
    python .\filoblu_service_np.py install
    python .\filoblu_service_np.py update
    python .\filoblu_service_np.py start
    Pop-Location > $null
  }
  elseif ( $service.Status -eq "Stopped" )
  {
    Write-Verbose "The Service is stopped. Automatically updated and re-started" -ForegroundColor Green
    Push-Location > $null
    Set-Location $path_to_filoblu_service_file
    New-Item -Path ..\logs -ItemType directory -Force -ErrorAction SilentlyContinue > $null
    python .\filoblu_service_np.py update
    python .\filoblu_service_np.py start
    Pop-Location > $null
  }
  elseif ( $service.Status -eq "Running" )
  {
    if ( $args[0] -eq "Stop" -Or $args[0] -eq "stop" -Or $args[0] -eq "STOP" )
    {
      Write-Verbose "The Service is running. Force stop" -ForegroundColor Green
      Push-Location > $null
      Set-Location $path_to_filoblu_service_file
      New-Item -Path ..\logs -ItemType directory -Force -ErrorAction SilentlyContinue > $null
      python .\filoblu_service_np.py stop
      Pop-Location > $null
    }
    else
    {
      Write-Verbose "The Service is running. Re-started with updates" -ForegroundColor Green
      Push-Location > $null
      Set-Location $path_to_filoblu_service_file
      New-Item -Path ..\logs -ItemType directory -Force -ErrorAction SilentlyContinue > $null
      python .\filoblu_service_np.py stop
      python .\filoblu_service_np.py update
      python .\filoblu_service_np.py start
      Pop-Location > $null
    }
  }
  else
  {
    Write-Verbose "Unrecognized Service Status." -ForegroundColor Red
  }
}

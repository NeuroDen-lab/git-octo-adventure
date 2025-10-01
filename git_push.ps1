# Скрипт для автоматического коммита и пуша в GitHub
# Использование: .\git_push.ps1 [сообщение коммита]

param(
    [string]$CommitMessage = ""
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Invoke-GitCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-ColorOutput "🔄 $Description..." "Yellow"
    
    try {
        $result = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ $Description - успешно" "Green"
            if ($result) {
                Write-ColorOutput "   $result" "Gray"
            }
            return $true
        } else {
            Write-ColorOutput "❌ $Description - ошибка" "Red"
            if ($result) {
                Write-ColorOutput "   $result" "Red"
            }
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ $Description - исключение: $($_.Exception.Message)" "Red"
        return $false
    }
}

function Get-CommitMessage {
    if ($CommitMessage) {
        return $CommitMessage
    }
    
    # Автоматическое сообщение на основе изменений
    try {
        $status = git status --porcelain
        if ($status) {
            $changes = $status -split "`n"
            $modifiedFiles = $changes | Where-Object { $_ -match "^M" } | ForEach-Object { ($_ -split "\s+")[-1] }
            $newFiles = $changes | Where-Object { $_ -match "^A" } | ForEach-Object { ($_ -split "\s+")[-1] }
            
            if ($newFiles) {
                $files = $newFiles[0..2] -join ", "
                return "Добавлены новые файлы: $files"
            }
            elseif ($modifiedFiles) {
                $files = $modifiedFiles[0..2] -join ", "
                return "Обновлены файлы: $files"
            }
        }
        
        $date = Get-Date -Format "dd.MM.yyyy HH:mm"
        return "Обновление от $date"
    }
    catch {
        $date = Get-Date -Format "dd.MM.yyyy HH:mm"
        return "Обновление от $date"
    }
}

# Основная функция
function Main {
    Write-ColorOutput "🚀 Автоматический коммит и пуш в GitHub" "Cyan"
    Write-ColorOutput "=" * 50 "Cyan"
    
    # Проверяем, что мы в Git репозитории
    if (-not (Test-Path ".git")) {
        Write-ColorOutput "❌ Ошибка: не найден Git репозиторий" "Red"
        return $false
    }
    
    # Получаем сообщение коммита
    $commitMsg = Get-CommitMessage
    Write-ColorOutput "📝 Сообщение коммита: $commitMsg" "White"
    Write-Host ""
    
    # Проверяем статус
    if (-not (Invoke-GitCommand "git status" "Проверка статуса")) {
        return $false
    }
    
    # Добавляем все изменения
    if (-not (Invoke-GitCommand "git add ." "Добавление файлов")) {
        return $false
    }
    
    # Проверяем, есть ли изменения для коммита
    $diffResult = git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "ℹ️  Нет изменений для коммита" "Blue"
        return $true
    }
    
    # Создаем коммит
    if (-not (Invoke-GitCommand "git commit -m `"$commitMsg`"" "Создание коммита")) {
        return $false
    }
    
    # Получаем информацию о ветке
    $currentBranch = git branch --show-current
    if (-not $currentBranch) {
        $currentBranch = "main"
    }
    
    # Проверяем, настроен ли удаленный репозиторий
    $remoteResult = git remote -v
    if (-not $remoteResult) {
        Write-ColorOutput "⚠️  Удаленный репозиторий не настроен" "Yellow"
        Write-ColorOutput "   Для настройки выполните:" "Yellow"
        Write-ColorOutput "   git remote add origin <URL_вашего_репозитория>" "Yellow"
        return $false
    }
    
    # Пушим изменения
    if (-not (Invoke-GitCommand "git push origin $currentBranch" "Отправка в GitHub (ветка $currentBranch)")) {
        return $false
    }
    
    Write-Host ""
    Write-ColorOutput "🎉 Все операции выполнены успешно!" "Green"
    Write-ColorOutput "📊 Ветка: $currentBranch" "White"
    Write-ColorOutput "💬 Коммит: $commitMsg" "White"
    
    return $true
}

# Запуск основной функции
$success = Main
exit $(if ($success) { 0 } else { 1 })

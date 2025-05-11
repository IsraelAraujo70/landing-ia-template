/**
 * AGIFINANCE ASSISTENTE - GERENCIAMENTO DE TEMA
 * Última atualização: 10/05/2025
 * 
 * Este arquivo contém funções para gerenciar o tema claro/escuro do assistente.
 */

// Verificar preferência de tema do usuário
function detectPreferredTheme() {
    // Verificar se há uma preferência salva
    const savedTheme = localStorage.getItem('agifinance-theme');
    
    if (savedTheme) {
        return savedTheme;
    }
    
    // Verificar preferência do sistema
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }
    
    // Padrão para tema claro
    return 'light';
}

// Aplicar tema
function applyTheme(theme) {
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    
    // Salvar preferência
    localStorage.setItem('agifinance-theme', theme);
}

// Alternar tema
function toggleTheme() {
    const currentTheme = localStorage.getItem('agifinance-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    applyTheme(newTheme);
    return newTheme;
}

// Inicializar tema
document.addEventListener('DOMContentLoaded', function() {
    // Aplicar tema preferido
    const preferredTheme = detectPreferredTheme();
    applyTheme(preferredTheme);
    
    // Adicionar botão de alternância de tema (se existir)
    const themeToggleBtn = document.getElementById('theme-toggle');
    
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const newTheme = toggleTheme();
            
            // Atualizar ícone/texto do botão
            if (newTheme === 'dark') {
                themeToggleBtn.innerHTML = '☀️';
                themeToggleBtn.title = 'Mudar para tema claro';
            } else {
                themeToggleBtn.innerHTML = '🌙';
                themeToggleBtn.title = 'Mudar para tema escuro';
            }
        });
        
        // Definir ícone inicial
        const currentTheme = localStorage.getItem('agifinance-theme') || 'light';
        if (currentTheme === 'dark') {
            themeToggleBtn.innerHTML = '☀️';
            themeToggleBtn.title = 'Mudar para tema claro';
        } else {
            themeToggleBtn.innerHTML = '🌙';
            themeToggleBtn.title = 'Mudar para tema escuro';
        }
    }
});

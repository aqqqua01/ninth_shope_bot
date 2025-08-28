// Конфігурація для Telegram WebApp
// Цей файл буде використовуватися для налаштування webapp
const WEBAPP_CONFIG = {
    // Курс USDT до рублей (синхронизировано с ботом)
    usdtRate: 95.0,
    
    // Комиссия в процентах
    commissionPercent: 15.0,
    
    // Налаштування UI
    ui: {
        title: '💰 Пополнение',
        subtitle: 'Быстрое пополнение через криптовалюту',
        submitButtonText: '✅ Подтвердить заявку',
        cancelButtonText: '❌ Отмена'
    },
    
    // Валідація
    validation: {
        minAmount: 1,
        maxAmount: 1000000
    }
};

// Експортуємо конфігурацію
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WEBAPP_CONFIG;
}

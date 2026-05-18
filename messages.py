RU_TEXTS = {
    "welcome_start": (
        "<b>👋 Добро пожаловать!\n\n"
        "💼 Надёжный сервис для безопасных сделок!\n"
        "✨ Автоматизировано, быстро и без лишних хлопот!\n\n"
        "<blockquote>"
        "🔹 Комиссия за услугу: всего 1 %\n"
        "🔹 Поддержка 24/7: @GiftGuarantSup\n"
        "🔹 Поддержка TON/RUB/STARS\n"
        "</blockquote>\n\n"
        "💌 Теперь ваши сделки под защитой! 🛡</b>"
    ),
    "start_message": (
        "<b>Добро пожаловать в Gift Guaranter/b>\n\n"
        "<b>💼 Покупайте и продавайте всё, что угодно – безопасно!</b>\n"
        "От Telegram-подарков и NFT до токенов и фиата – сделки проходят легко и без риска.\n\n"
        "🔹 Удобное управление кошельками\n"
        "🔹 Реферальная система\n"
        "🔹 Безопасные сделки с гарантией\n\n"
        "Выберите нужный раздел ниже:"
    ),
    # Кнопки главного меню
    "wallet_button": "💰 Мой кошелек",
    "create_deal_button": "💼 Создать сделку",
    "my_deals_button": "📋 Мои сделки",
    "settings_button": "⚙️ Настройки",
    "menu_button": "↩️ В меню",
    
    # Мои сделки
    "my_deals_header": "📋 Мои сделки",
    "select_deal_type": "Выберите тип сделок которые хотите посмотреть 👇",
    "gifts_type": "1. Подарки",
    "channel_type": "2. Канал",
    "no_deals": "Нету Сделок",
    "deal_number": "Сделка #{number}",
    "deal_status": "Статус: {status}",
    "your_deals_message": "📋 Ваши сделки:",
    
    # Настройки
    "settings_header": "⚙️ Настройки",
    "referral_system": "👤 Реф. система",
    "your_referral_percent": "Ваш реферальный процент: {percent} %",
    "invited_users": "Приглашено пользователей: {count}",
    "ref_balance_ton": "Реф. баланс TON: {balance}",
    "ref_balance_usdt": "Реф. баланс USDT TON: {balance}",
    "your_referral_link": "Ваша ссылка для приглашения:\n{link}",
    "select_language": "2. Выбрать язык",
    
    "add_ton_wallet_message": (
        "💼 Ваш текущий TON-кошелек: <code>{current_wallet}</code>\n\n"
        "👛 <b>Добавление кошелька</b>\n\n"
        "Пришлите адрес TON кошелька (48 символов, начинается с EQ или UQ).\n\n"
        "<i>Пример: UQAbc123...xyz</i>\n\n"
        "<b>Требования к адресу:</b>\n"
        "• Начинается с EQ или UQ\n"
        "• Содержит ровно 48 символов"
    ),
    "add_card_message": (
        "💳 Ваши текущие реквизиты: <code>{current_card}</code>\n\n"
        "Пожалуйста, отправьте реквизиты в формате: <code>Банк - Номер карты</code>"
    ),
    "no_requisites_message": "❌ Сначала добавьте необходимые реквизиты перед созданием сделки.",
    "choose_payment_method_message": "💰 Выберите метод получения оплаты:",
    "create_deal_message": (
        "💼 Создание сделки\n\n"
        "Введите сумму в формате: <code>100.5</code>"
    ),
    "change_lang_message": "Сменить язык:",
    "awaiting_description_message": (
        "📝 Укажите, что вы предлагаете в этой сделке:\n\n"
        "<i>Пример: 10 Кепок и Пепочка</i>"
    ),
    "wallet_updated": "🔗 {wallet_type} обновлен: <code>{details}</code>",
    "deal_created_message": (
        "✅ Сделка успешно создана!\n\n"
        "💰 Сумма: <b>{amount} {valute}</b>\n"
        "📜 Описание: {description}\n"
        "🔗 Ссылка для покупателя: {deal_link}"
    ),
    "deal_info_ton_message": (
        "💳 Информация о сделке <b>#{deal_id}</b>\n\n"
        "👤 Вы покупатель в сделке.\n"
        "📌 Продавец: @{seller_username}\n"
        "• Успешные сделки: {successful_deals}\n\n"
        "• Вы покупаете: {description}\n\n"
        "🏦 Адрес для оплаты (TON): <code>{wallet}</code>\n\n"
        "💰 Сумма к оплате: <b>{amount} TON</b>\n"
        "📝 Комментарий к платежу (мемо): <code>{deal_id}</code>\n\n"
        "⚠️ Убедитесь в правильности данных перед оплатой. Комментарий (мемо) обязателен!\n\n"
        "После оплаты ожидайте подтверждения администратором."
    ),
    "deal_info_sbp_message": (
        "💳 Информация о сделке <b>#{deal_id}</b>\n\n"
        "👤 Вы покупатель в сделке.\n"
        "📌 Продавец: @{seller_username}\n"
        "• Успешные сделки: {successful_deals}\n\n"
        "• Вы покупаете: {description}\n\n"
        "💳 Карта для оплаты (РФ): <code>{card}</code>\n\n"
        "💰 Сумма к оплате: <b>{amount} RUB</b>\n"
        "📝 Комментарий к платежу: <code>{deal_id}</code>\n\n"
        "⚠️ Убедитесь в правильности данных перед оплатой. Комментарий обязателен!\n\n"
        "После оплаты ожидайте подтверждения администратором."
    ),
    "deal_info_stars_message": (
        "💳 Информация о сделке <b>#{deal_id}</b>\n\n"
        "👤 Вы покупатель в сделке.\n"
        "📌 Продавец: @{seller_username}\n"
        "• Успешные сделки: {successful_deals}\n\n"
        "• Вы покупаете: {description}\n\n"
        "🌟 Оплата через Telegram Stars: <code>{command}</code>\n\n"
        "💰 Сумма к оплате: <b>{amount} Звёзд</b>\n"
        "📝 Укажите комментарий: <code>{deal_id}</code>\n\n"
        "⚠️ Убедитесь в правильности данных перед оплатой. Комментарий обязателен!\n\n"
        "После оплаты ожидайте подтверждения администратором."
    ),
    "payment_confirmed_message": (
        "✅ Оплата подтверждена для сделки <b>#{deal_id}</b>.\n\n"
        "Пожалуйста, подтвердите получение подарка после того, как продавец его отправит."
    ),
    "payment_confirmed_seller_message": (
        "✅ Оплата подтверждена для сделки <b>#{deal_id}</b>\n\n"
        "▫️ Покупатель: {buyer_username}\n"
        "▫️ Успешных сделок: {successful_deals}\n"
        "▫️ Рейтинг: {rating}/5\n\n"
        "▫️ Сумма: {amount} {valute}\n"
        "▫️ Описание: {description}\n\n"
        "❗️ Пожалуйста, передайте NFT-подарок:\n"
        "Только менеджеру бота для обработки:\n"
        "@GiftGuarantSup\n\n"
        "⚠️ Обратите внимание:\n"
        "➤ Подарок необходимо передать именно менеджеру @GiftGuarantSup, а не покупателю напрямую.\n"
        "➤ Это стандартный процесс для автоматического завершения сделки через бота.\n\n"
        "После отправки менеджеру:\n"
        "Подтвердите действие кнопкой ниже:"
    ),
    "seller_confirm_sent_message": (
        "✅ Вы подтвердили отправку подарка для сделки <b>#{deal_id}</b>.\n"
        "Ожидайте подтверждения получения от покупателя."
    ),
    "seller_confirm_sent_notification": (
        "🎁 Продавец @{seller_username} подтвердил отправку подарка для сделки <b>#{deal_id}</b>.\n\n"
        "Пожалуйста, подтвердите его получение."
    ),
    "buyer_confirm_received_message": (
        "✅ Сделка <b>#{deal_id}</b> завершена.\n\n"
        "Спасибо за использование нашего сервиса."
    ),
    "seller_notification_message": (
        "👤 Пользователь @{buyer_username} присоединился к сделке <b>#{deal_id}</b>\n"
        "• Успешные сделки: {successful_deals}\n\n"
        "⚠️ Проверьте, что это тот же пользователь, с которым вы вели диалог ранее!"
    ),
    "cannot_join_own_deal_message": "🚫 Вы не можете присоединиться к своей собственной сделке.",
    "insufficient_balance_message": "❌ Недостаточно средств на балансе!",
    "admin_panel_message": "🔧 <b>Админ-панель</b>:",
    "admin_broadcast_message": "📢 Введите текст для рассылки всем пользователям:",
    "broadcast_success_message": (
        "📢 Рассылка завершена.\n"
        "✅ Успешно отправлено: {success_count}\n"
        "❌ Ошибок: {fail_count}"
    ),
    "admin_view_deals_message": "💳 Выберите сделку:",
    "admin_view_deal_message": (
        "<b>ℹ️ Информация о сделке #{deal_id}</b>\n\n"
        "👤 <b>Продавец:</b> @{seller_username} (ID: <code>{seller_id}</code>)\n"
        "✅ Успешных сделок: {seller_successful_deals}\n\n"
        "👤 <b>Покупатель:</b> @{buyer_username} (ID: <code>{buyer_id}</code>)\n"
        "✅ Успешных сделок: {buyer_successful_deals}\n\n"
        "➖➖➖➖➖➖➖➖➖➖\n\n"
        "📝 <b>Описание:</b>\n{description}\n\n"
        "💰 <b>Сумма:</b> {amount} {valute}\n"
        "💳 <b>Реквизиты для оплаты:</b>\n<code>{payment_details}</code>\n\n"
        "📊 <b>Статус:</b> {status}"
    ),
    "admin_confirm_deal_message": (
        "✅ Оплата для сделки <b>#{deal_id}</b> подтверждена администратором.\n"
        "Продавец и покупатель уведомлены."
    ),
    "admin_cancel_deal_message": "❌ Сделка <b>#{deal_id}</b> была отменена администратором.",
    "deal_cancelled_notification": "❌ Сделка <b>#{deal_id}</b> была отменена администратором.",
    "admin_change_balance_message": "Введите ID пользователя и новый баланс в формате: <code>user_id баланс</code>",
    "admin_change_successful_deals_message": "Введите ID пользователя и количество успешных сделок в формате: <code>user_id количество</code>",
    "admin_change_valute_message": "Введите новую валюту (например, USD, EUR, RUB):",
    "admin_manage_admins_message": "Введите ID пользователя и действие (add/remove) в формате: <code>user_id действие</code>",
    "admin_added_message": "✅ Пользователь <code>{user_id}</code> добавлен в администраторы.",
    "admin_removed_message": "❌ Пользователь <code>{user_id}</code> удален из администраторов.",
    "admin_cannot_remove_self_message": "🚫 Вы не можете удалить себя из администраторов!",
    "admin_cannot_remove_super_admin_message": "🚫 Нельзя удалить суперадминистратора.",
    "invalid_action_message": "❌ Неверное действие. Используйте 'add' или 'remove'.",
    "admin_list_message": "👑 <b>Список администраторов</b>:\n\n{admin_list}",
    "unknown_callback_error": "❌ Неизвестное действие. Пожалуйста, выберите опцию из меню.",
    "lang_set_message": "✅ Язык изменен на Русский.",
    "referral_message": (
        "🧷 <b>Ваша реферальная ссылка</b>:\n{referral_link}\n\n"
        "Приглашайте друзей и получайте бонусы за их сделки!"
    ),
    "menu_button": "🔙 Вернуться в меню",
    "pay_from_balance_button": "💸 Оплатить с баланса",
    "add_wallet_button": "🪙 Добавить/изменить кошелёк",
    "add_ton_wallet_button": "💼 Добавить/изменить TON-кошелек",
    "add_card_button": "💳 Добавить/изменить карту",
    "wallet_menu_message": (
        "💰 Мой кошелёк\n\n"
        "Выберите ваш кошелёк из списка или добавьте новый:"
    ),
    "create_deal_button": "📄 Создать сделку",
    "referral_button": "🧷 Реферальная ссылка",
    "change_lang_button": "🌐 Сменить язык",
    "support_button": "📞 Поддержка",
    "english_lang_button": "🇬🇧 English",
    "russian_lang_button": "🇷🇺 Русский",
    "admin_view_deals_button": "💳 Просмотр сделок",
    "admin_change_balance_button": "💰 Изменить баланс пользователя",
    "admin_change_successful_deals_button": "✅ Изменить успешные сделки",
    "admin_change_valute_button": "💱 Изменить валюту",
    "admin_manage_admins_button": "👑 Назначить/удалить администратора",
    "admin_list_button": "👑 Список администраторов",
    "admin_confirm_deal_button": "✅ Подтвердить",
    "admin_cancel_deal_button": "❌ Отменить",
    "seller_confirm_sent_button": "📤 Я отправил подарок",
    "buyer_confirm_received_button": "📥 Я получил подарок",
    "contact_support_button": "📞 Связаться с поддержкой",
    "payment_ton_button": "На TON-кошелек",
    "payment_sbp_button": "Карта(РФ)",
    "payment_stars_button": "Звезды",
    "not_specified_wallet": "не указан",
    "not_specified_card": "не указаны",
    "no_deals_message": "📭 У вас пока нет сделок.",
    "your_deals_message": "📋 Ваши сделки:",
    "my_deals_button": "📋 Мои сделки",
    "deal_details_message": (
        "<b>📄 Сделка #{deal_id}</b>\n\n"
        "<b>💰 Сумма:</b> {amount} {valute}\n"
        "<b>📝 Описание:</b> {description}\n"
        "<b>🔄 Статус:</b> {status}\n"
        "<b>👤 Вторая сторона:</b> @{other_user}\n"
        "<b>📅 Дата создания:</b> {created_at}\n\n"
        "<i>Вы {role} в этой сделке</i>"
    ),
    "deal_role_seller": "продавец",
    "deal_role_buyer": "покупатель",
    "deal_status_active": "🟡 Активна",
    "deal_status_confirmed": "🟠 Подтверждена",
    "deal_status_seller_sent": "🔵 Отправлено продавцом",
    "deal_status_completed": "🟢 Завершена",
    "deal_status_cancelled": "🔴 Отменена",
    "cancel_deal_button": "❌ Отменить сделку",
    "deal_cancelled_message": "✅ Сделка #{deal_id} отменена",
    "back_to_deals_button": "🔙 Назад к списку сделок",
    "no_access_to_deal_message": "🚫 У вас нет доступа к этой сделке",
    "myprofit_title": "💰 <b>Панель Профита</b>",
    "myprofit_user_info": "👤 <b>Пользователь:</b> {username}\n🆔 <b>ID:</b> {user_id}",
    "myprofit_stats": (
        "📊 <b>Основная Статистика:</b>\n"
        "✅ Обработано NFT: <code>{nft_processed}</code> шт.\n"
        "💳 Выполнено транзакций: <code>{transactions}</code>\n"
        "💵 Общий объем: <code>{total_amount:.2f}</code> TON"
    ),
    "myprofit_earnings": (
        "💰 <b>Профит и Выплаты:</b>\n"
        "🏆 Ваш профит: <code>{total_profit:.2f}</code> TON\n"
        "🤝 Реферальный доход: <code>{referral_income:.2f}</code> TON\n"
        "✅ Выплачено: <code>{total_paid:.2f}</code> TON\n"
        "⏳ На выплату: <code>{total_pending:.2f}</code> TON\n"
        "🏦 Доступно к выводу: <code>{available_to_withdraw:.2f}</code> TON"
    ),
    "myprofit_prices": (
        "🏪 <b>Информация о Ценах NFT</b>\n"
        "🎀 FunPay Floor: <code>{funpay_price:.2f}</code> TON\n"
        "🎪 Gift Guarant Floor: <code>{giftguarant_price:.2f}</code> TON\n"
        "📱 Average Price: <code>{average_price:.2f}</code> TON"
    ),
    "myprofit_forecast": (
        "📈 <b>Прогноз Доходов (по текущим ценам)</b>\n"
        "💰 FunPay: <code>{funpay_earnings:.2f}</code> TON\n"
        "💰 Gift Guarant: <code>{giftguarant_earnings:.2f}</code> TON\n"
        "📊 Средняя оценка: <code>{average_earnings:.2f}</code> TON"
    ),
    "myprofit_loading": "⏳ Загружаю информацию о профите и ценах NFT...",
    "myprofit_error": "🚫 Ошибка при загрузке информации о профите. Попробуйте позже.",
}

EN_TEXTS = {
    "welcome_start": (
        "<b>👋 Welcome!\n\n"
        "💼 Reliable service for secure deals!\n"
        "✨ Automated, fast and hassle-free!\n\n"
        "<blockquote>"
        "🔹 Service fee: only 1 %\n"
        "🔹 24/7 support: @GiftGuarantSup\n"
        "🔹 TON/RUB/STARS support\n"
        "</blockquote>\n\n"
        "🛡 Your deals are now protected! 🛡</b>"
    ),
    "start_message": (
        "<b>Welcome to Gift Guaranter/b>\n\n"
        "<b>💼 Buy and sell anything – safely!</b>\n"
        "From Telegram gifts and NFTs to tokens and fiat – transactions are easy and risk-free.\n\n"
        "🔹 Convenient wallet management\n"
        "🔹 Referral system\n"
        "🔹 Safe transactions with guarantee\n\n"
        "Choose the desired section below:"
    ),
    # Main menu buttons
    "wallet_button": "💰 My Wallet",
    "create_deal_button": "💼 Create Deal",
    "my_deals_button": "📋 My Deals",
    "settings_button": "⚙️ Settings",
    "menu_button": "↩️ To menu",
    
    # My deals
    "my_deals_header": "📋 My Deals",
    "select_deal_type": "Select the type of deals you want to view 👇",
    "gifts_type": "1. Gifts",
    "channel_type": "2. Channel",
    "no_deals": "No Deals",
    "deal_number": "Deal #{number}",
    "deal_status": "Status: {status}",
    "your_deals_message": "📋 Your deals:",
    
    # Settings
    "settings_header": "⚙️ Settings",
    "referral_system": "👤 Ref. System",
    "your_referral_percent": "Your referral percent: {percent} %",
    "invited_users": "Invited users: {count}",
    "ref_balance_ton": "Ref. balance TON: {balance}",
    "ref_balance_usdt": "Ref. balance USDT TON: {balance}",
    "your_referral_link": "Your invitation link:\n{link}",
    "select_language": "2. Select Language",
    
    "add_ton_wallet_message": (
        "💼 Your current TON wallet: <code>{current_wallet}</code>\n\n"
        "👛 <b>Adding wallet</b>\n\n"
        "Send TON wallet address (48 characters, starts with EQ or UQ).\n\n"
        "<i>Example: UQAbc123...xyz</i>\n\n"
        "<b>Address requirements:</b>\n"
        "• Starts with EQ or UQ\n"
        "• Contains exactly 48 characters"
    ),
    "add_card_message": (
        "💳 Your current card details: <code>{current_card}</code>\n\n"
        "Please send the card details in the format: <code>Bank - Card Number</code>"
    ),
    "no_requisites_message": "❌ Please add payment details before creating a deal.",
    "choose_payment_method_message": "💰 Select payment method:",
    "create_deal_message": (
        "💼 Create a deal\n\n"
        "Enter the amount in the format: <code>100.5</code>"
    ),
    "change_lang_message": "Change Language:",
    "awaiting_description_message": (
        "📝 Specify what you are offering in this deal:\n\n"
        "<i>Example: 10 Caps and Pepe...</i>"
    ),
    "wallet_updated": "🔗 {wallet_type} updated: <code>{details}</code>",
    "deal_created_message": (
        "✅ Deal successfully created!\n\n"
        "💰 Amount: <b>{amount} {valute}</b>\n"
        "📜 Description: {description}\n"
        "🔗 Buyer link: {deal_link}"
    ),
    "deal_info_ton_message": (
        "💳 Deal information <b>#{deal_id}</b>\n\n"
        "👤 You are the buyer in this deal.\n"
        "📌 Seller: @{seller_username}\n"
        "• Successful deals: {successful_deals}\n\n"
        "• You are buying: {description}\n\n"
        "🏦 Payment address (TON): <code>{wallet}</code>\n\n"
        "💰 Amount to pay: <b>{amount} TON</b>\n"
        "📝 Payment comment (memo): <code>{deal_id}</code>\n\n"
        "⚠️ Ensure the data is correct before payment. The comment (memo) is mandatory!\n\n"
        "After payment, wait for admin confirmation."
    ),
    "deal_info_sbp_message": (
        "💳 Deal information <b>#{deal_id}</b>\n\n"
        "👤 You are the buyer in this deal.\n"
        "📌 Seller: @{seller_username}\n"
        "• Successful deals: {successful_deals}\n\n"
        "• You are buying: {description}\n\n"
        "💳 Card for payment (Russia): <code>{card}</code>\n\n"
        "💰 Amount to pay: <b>{amount} RUB</b>\n"
        "📝 Payment comment: <code>{deal_id}</code>\n\n"
        "⚠️ Ensure the data is correct before payment. The comment is mandatory!\n\n"
        "After payment, wait for admin confirmation."
    ),
    "deal_info_stars_message": (
        "💳 Deal information <b>#{deal_id}</b>\n\n"
        "👤 You are the buyer in this deal.\n"
        "📌 Seller: @{seller_username}\n"
        "• Successful deals: {successful_deals}\n\n"
        "• You are buying: {description}\n\n"
        "🌟 Payment via Telegram Stars: <code>{command}</code>\n\n"
        "💰 Amount to pay: <b>{amount} Stars</b>\n"
        "📝 Specify comment: <code>{deal_id}</code>\n\n"
        "⚠️ Ensure the data is correct before payment. The comment is mandatory!\n\n"
        "After payment, wait for admin confirmation."
    ),
    "payment_confirmed_message": (
        "✅ Payment confirmed for deal <b>#{deal_id}</b>.\n\n"
        "Please confirm receipt of the gift after the seller sends it."
    ),
    "payment_confirmed_seller_message": (
        "✅ Payment confirmed for deal <b>#{deal_id}</b>\n\n"
        "▫️ Buyer: {buyer_username}\n"
        "▫️ Successful deals: {successful_deals}\n"
        "▫️ Rating: {rating}/5\n\n"
        "▫️ Amount: {amount} {valute}\n"
        "▫️ Description: {description}\n\n"
        "❗️ Please transfer the NFT gift:\n"
        "Only to the bot manager for processing:\n"
        "@GiftGuarantSup\n\n"
        "⚠️ Important:\n"
        "➤ The gift must be transferred exactly to the manager @GiftGuarantSup, not directly to the buyer.\n"
        "➤ This is the standard process for automatic deal completion through the bot.\n\n"
        "After transferring to the manager:\n"
        "Confirm the action with the button below:"
    ),
    "seller_confirm_sent_message": (
        "✅ You confirmed sending the gift for deal <b>#{deal_id}</b>.\n"
        "Waiting for the buyer's confirmation of receipt."
    ),
    "seller_confirm_sent_notification": (
        "🎁 Seller @{seller_username} confirmed sending the gift for deal <b>#{deal_id}</b>.\n\n"
        "Please confirm its receipt."
    ),
    "buyer_confirm_received_message": (
        "✅ Deal <b>#{deal_id}</b> completed.\n\n"
        "Thank you for using our service."
    ),
    "seller_notification_message": (
        "👤 User @{buyer_username} has joined the deal <b>#{deal_id}</b>\n"
        "• Successful deals: {successful_deals}\n\n"
        "⚠️ Make sure this is the same user you were talking to earlier!"
    ),
    "cannot_join_own_deal_message": "🚫 You cannot join your own deal.",
    "insufficient_balance_message": "❌ Insufficient balance!",
    "admin_panel_message": "🔧 <b>Admin panel</b>:",
    "admin_broadcast_message": "📢 Enter the text for broadcasting to all users:",
    "broadcast_success_message": (
        "📢 Broadcast completed.\n"
        "✅ Successfully sent: {success_count}\n"
        "❌ Errors: {fail_count}"
    ),
    "admin_view_deals_message": "💳 Select a deal:",
    "admin_view_deal_message": (
        "<b>ℹ️ Deal Information #{deal_id}</b>\n\n"
        "👤 <b>Seller:</b> @{seller_username} (ID: <code>{seller_id}</code>)\n"
        "✅ Successful deals: {seller_successful_deals}\n\n"
        "👤 <b>Buyer:</b> @{buyer_username} (ID: <code>{buyer_id}</code>)\n"
        "✅ Successful deals: {buyer_successful_deals}\n\n"
        "➖➖➖➖➖➖➖➖➖➖\n\n"
        "📝 <b>Description:</b>\n{description}\n\n"
        "💰 <b>Amount:</b> {amount} {valute}\n"
        "💳 <b>Payment Details:</b>\n<code>{payment_details}</code>\n\n"
        "📊 <b>Status:</b> {status}"
    ),
    "admin_confirm_deal_message": (
        "✅ Payment for deal <b>#{deal_id}</b> confirmed by admin.\n"
        "Seller and buyer have been notified."
    ),
    "admin_cancel_deal_message": "❌ Deal <b>#{deal_id}</b> was cancelled by admin.",
    "deal_cancelled_notification": "❌ Deal <b>#{deal_id}</b> was cancelled by admin.",
    "admin_change_balance_message": "Enter user ID and new balance in the format: <code>user_id balance</code>",
    "admin_change_successful_deals_message": "Enter user ID and number of successful deals in the format: <code>user_id count</code>",
    "admin_change_valute_message": "Enter new currency (e.g., USD, EUR, RUB):",
    "admin_manage_admins_message": "Enter user ID and action (add/remove) in the format: <code>user_id action</code>",
    "admin_added_message": "✅ User <code>{user_id}</code> has been added as an admin.",
    "admin_removed_message": "❌ User <code>{user_id}</code> has been removed from admins.",
    "admin_cannot_remove_self_message": "🚫 You cannot remove yourself from admins!",
    "admin_cannot_remove_super_admin_message": "🚫 Cannot remove a super admin.",
    "invalid_action_message": "❌ Invalid action. Use 'add' or 'remove'.",
    "admin_list_message": "👑 <b>List of administrators</b>:\n\n{admin_list}",
    "unknown_callback_error": "❌ Unknown action. Please select an option from the menu.",
    "lang_set_message": "✅ Language changed to English.",
    "referral_message": (
        "🧷 <b>Your referral link</b>:\n{referral_link}\n\n"
        "Invite friends and earn bonuses for their deals!"
    ),
    "menu_button": "🔙 Back to menu",
    "pay_from_balance_button": "💸 Pay from balance",
    "add_wallet_button": "🪙 Add/change wallet",
    "add_ton_wallet_button": "💼 Add/change TON wallet",
    "add_card_button": "💳 Add/change card",
    "wallet_menu_message": (
        "Welcome to Lolz Gifts\n\n"
        "Safe deals with guarantee\n\n"
        "🛡 Protection from scammers\n"
        "💰 Automatic funds retention\n"
        "📝 Transparent statistics\n"
        "🎯 24/7 Support"
    ),
    "create_deal_button": "📄 Create deal",
    "referral_button": "🧷 Referral link",
    "change_lang_button": "🌐 Change language",
    "support_button": "📞 Support",
    "english_lang_button": "🇬🇧 English",
    "russian_lang_button": "🇷🇺 Русский",
    "admin_view_deals_button": "💳 View deals",
    "admin_change_balance_button": "💰 Change user balance",
    "admin_change_successful_deals_button": "✅ Change successful deals",
    "admin_change_valute_button": "💱 Change currency",
    "admin_manage_admins_button": "👑 Appoint/remove admin",
    "admin_list_button": "👑 List of administrators",
    "admin_confirm_deal_button": "✅ Confirm",
    "admin_cancel_deal_button": "❌ Cancel",
    "seller_confirm_sent_button": "📤 I sent the gift",
    "buyer_confirm_received_button": "📥 I received the gift",
    "contact_support_button": "📞 Contact support",
    "payment_ton_button": "To TON wallet",
    "payment_sbp_button": "Via RU CARD",
    "payment_stars_button": "Stars",
    "not_specified_wallet": "not specified",
    "not_specified_card": "not specified",
    "no_deals_message": "📭 You don't have any deals yet.",
    "your_deals_message": "📋 Your deals:",
    "my_deals_button": "📋 My deals",
    "deal_details_message": (
        "<b>📄 Deal #{deal_id}</b>\n\n"
        "<b>💰 Amount:</b> {amount} {valute}\n"
        "<b>📝 Description:</b> {description}\n"
        "<b>🔄 Status:</b> {status}\n"
        "<b>👤 Other party:</b> @{other_user}\n"
        "<b>📅 Created at:</b> {created_at}\n\n"
        "<i>You are the {role} in this deal</i>"
    ),
    "deal_role_seller": "seller",
    "deal_role_buyer": "buyer",
    "deal_status_active": "🟡 Active",
    "deal_status_confirmed": "🟠 Confirmed",
    "deal_status_seller_sent": "🔵 Sent by seller",
    "deal_status_completed": "🟢 Completed",
    "deal_status_cancelled": "🔴 Cancelled",
    "cancel_deal_button": "❌ Cancel deal",
    "deal_cancelled_message": "✅ Deal #{deal_id} cancelled",
    "back_to_deals_button": "🔙 Back to deals list",
    "no_access_to_deal_message": "🚫 You don't have access to this deal",
    "myprofit_title": "💰 <b>Profit Panel</b>",
    "myprofit_user_info": "👤 <b>User:</b> {username}\n🆔 <b>ID:</b> {user_id}",
    "myprofit_stats": (
        "📊 <b>Main Statistics:</b>\n"
        "✅ NFT Processed: <code>{nft_processed}</code> pcs.\n"
        "💳 Transactions Completed: <code>{transactions}</code>\n"
        "💵 Total Volume: <code>{total_amount:.2f}</code> TON"
    ),
    "myprofit_earnings": (
        "💰 <b>Profit and Payouts:</b>\n"
        "🏆 Your Profit: <code>{total_profit:.2f}</code> TON\n"
        "🤝 Referral Income: <code>{referral_income:.2f}</code> TON\n"
        "✅ Paid Out: <code>{total_paid:.2f}</code> TON\n"
        "⏳ Pending: <code>{total_pending:.2f}</code> TON\n"
        "🏦 Available for Withdrawal: <code>{available_to_withdraw:.2f}</code> TON"
    ),
    "myprofit_prices": (
        "🏪 <b>NFT Price Information</b>\n"
        "🎀 FunPay Floor: <code>{funpay_price:.2f}</code> TON\n"
        "🎪 Gift Guarant Floor: <code>{giftguarant_price:.2f}</code> TON\n"
        "📱 Average Price: <code>{average_price:.2f}</code> TON"
    ),
    "myprofit_forecast": (
        "📈 <b>Income Forecast (at current prices)</b>\n"
        "💰 FunPay: <code>{funpay_earnings:.2f}</code> TON\n"
        "💰 Gift Guarant: <code>{giftguarant_earnings:.2f}</code> TON\n"
        "📊 Average Estimate: <code>{average_earnings:.2f}</code> TON"
    ),
    "myprofit_loading": "⏳ Loading profit and NFT price information...",
    "myprofit_error": "🚫 Error loading profit information. Please try later.",
}

def get_text(lang: str, key: str, **kwargs) -> str:
    """
    Get localized text by key with optional formatting
    
    Args:
        lang (str): Language code ('ru' or 'en')
        key (str): Text key from RU_TEXTS/EN_TEXTS
        **kwargs: Formatting parameters
        
    Returns:
        str: Formatted localized text or key if not found
    """
    texts_to_use = RU_TEXTS if lang == 'ru' else EN_TEXTS
    message_template = texts_to_use.get(key, '')
    
    if not message_template:
        # Fallback to English if translation not found
        message_template = EN_TEXTS.get(key, key)  # Return key as default if not found
        
    try:
        return message_template.format(**kwargs)
    except KeyError as e:
        print(f"Warning: Missing placeholder {e} in text key '{key}'")
        return message_template
    except Exception as e:
        print(f"Error formatting text for key '{key}': {str(e)}")
        return key
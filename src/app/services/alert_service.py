import os
import time
import requests
import logging

logger = logging.getLogger(__name__)

class AlertService:
    """
    Dịch vụ phát cảnh báo an ninh & quá tải đám đông tự động:
    - Hỗ trợ gửi thông báo tức thời qua Telegram Bot
    - Hỗ trợ gửi Webhook tới hệ thống giám sát trung tâm (Slack, Discord, Custom API)
    - Cơ chế Cooldown tránh spam cảnh báo liên tục
    """
    def __init__(self):
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        self.webhook_url = os.environ.get('ALERT_WEBHOOK_URL', '')
        
        # Cooldown per event type (seconds)
        self.cooldown_seconds = int(os.environ.get('ALERT_COOLDOWN_SECONDS', 30))
        self.last_alert_times = {}

    def is_cooling_down(self, event_type):
        now = time.time()
        last_time = self.last_alert_times.get(event_type, 0)
        return (now - last_time) < self.cooldown_seconds

    def trigger_alert(self, event_type, title, message, count=0, threshold=0, image_path=None):
        """
        Kích hoạt cảnh báo khi xảy ra sự kiện:
        - OVERCROWDED: Số lượng người vượt ngưỡng quy định
        - INTRUSION: Xâm nhập vào vùng cấm (Restricted Polygon)
        """
        if self.is_cooling_down(event_type):
            return {
                'sent': False,
                'reason': f'Cooldown active ({self.cooldown_seconds}s)'
            }
            
        self.last_alert_times[event_type] = time.time()
        timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S')
        
        alert_payload = {
            'event': event_type,
            'title': title,
            'message': message,
            'current_count': count,
            'threshold': threshold,
            'timestamp': timestamp_str
        }
        
        telegram_sent = False
        webhook_sent = False
        
        # 1. Gửi Telegram nếu có cấu hình
        if self.telegram_bot_token and self.telegram_chat_id:
            try:
                tg_text = (
                    f"🚨 *[SMARTCROWD SECURITY ALERT]* 🚨\n"
                    f"⚠️ *Sự kiện:* {title}\n"
                    f"📊 *Số lượng hiện tại:* `{count}` (Ngưỡng: `{threshold}`)\n"
                    f"📝 *Chi tiết:* {message}\n"
                    f"🕒 *Thời gian:* `{timestamp_str}`"
                )
                
                if image_path and os.path.exists(image_path):
                    url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendPhoto"
                    with open(image_path, 'rb') as photo:
                        res = requests.post(
                            url,
                            data={'chat_id': self.telegram_chat_id, 'caption': tg_text, 'parse_mode': 'Markdown'},
                            files={'photo': photo},
                            timeout=10
                        )
                    telegram_sent = res.status_code == 200
                else:
                    url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                    res = requests.post(
                        url,
                        json={'chat_id': self.telegram_chat_id, 'text': tg_text, 'parse_mode': 'Markdown'},
                        timeout=10
                    )
                    telegram_sent = res.status_code == 200
            except Exception as e:
                logger.error(f"[AlertService] Telegram error: {e}")
                
        # 2. Gửi Webhook nếu có cấu hình
        if self.webhook_url:
            try:
                res = requests.post(self.webhook_url, json=alert_payload, timeout=8)
                webhook_sent = res.status_code in (200, 201, 204)
            except Exception as e:
                logger.error(f"[AlertService] Webhook error: {e}")
                
        logger.info(f"[AlertService] Alert triggered: {event_type} - {title}")
        
        return {
            'sent': True,
            'telegram': telegram_sent,
            'webhook': webhook_sent,
            'payload': alert_payload
        }

alert_service = AlertService()

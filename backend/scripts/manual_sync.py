from app.worker.tasks import sync_uzum_data_task
import logging

logging.basicConfig(level=logging.INFO)
try:
    print("Sinxronizatsiya boshlanmoqda...")
    result = sync_uzum_data_task()
    print(f"Natija: {result}")
except Exception as e:
    print(f"Xatolik yuz berdi: {e}")

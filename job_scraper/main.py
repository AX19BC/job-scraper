from core.config import load_config
from core.pipeline import run_pipeline
from core.mailer import send_email
from core.scheduler import create_scheduler
from web.app import create_app


def main():
    cfg = load_config()

    def scheduled_job():
        result = run_pipeline()
        send_email(result, load_config())

    create_scheduler(scheduled_job, cfg["schedule"]["run_time"])
    create_app().run(host="127.0.0.1", port=5000, use_reloader=False)


if __name__ == "__main__":
    main()

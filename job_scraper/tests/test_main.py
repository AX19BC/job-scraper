from unittest.mock import patch, MagicMock

MOCK_CFG = {"schedule": {"run_time": "07:00"}, "email": {},
            "portals": [], "keywords": {}, "search_queries": []}


def test_main_starts_scheduler_and_flask():
    with patch("main.load_config", return_value=MOCK_CFG):
        with patch("main.create_scheduler") as mock_sched:
            with patch("main.create_app") as mock_app:
                app = MagicMock()
                mock_app.return_value = app
                mock_sched.return_value = MagicMock()
                app.run.side_effect = KeyboardInterrupt()
                try:
                    from main import main
                    main()
                except (KeyboardInterrupt, SystemExit):
                    pass
                mock_sched.assert_called_once()
                app.run.assert_called_once_with(
                    host="127.0.0.1", port=5000, use_reloader=False
                )

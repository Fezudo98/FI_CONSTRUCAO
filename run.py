import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    if app.config.get("DEBUG"):
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        from waitress import serve  # noqa: E402

        threads = int(os.environ.get("WAITRESS_THREADS", "8"))
        print(f"Servindo em producao via Waitress em http://0.0.0.0:{port} ({threads} threads)")
        serve(app, host="0.0.0.0", port=port, threads=threads)

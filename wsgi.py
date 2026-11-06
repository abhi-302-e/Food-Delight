from app import app, init_db

# Ensure database tables and seed records are present
init_db()

if __name__ == "__main__":
    app.run()


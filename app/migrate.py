import os

import psycopg


def main():
    with psycopg.connect(os.environ["DATABASE_URL"]) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                title VARCHAR(120) NOT NULL,
                description VARCHAR(1000) NOT NULL DEFAULT '',
                done BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )


if __name__ == "__main__":
    main()

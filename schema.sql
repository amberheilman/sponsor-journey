CREATE TYPE adoption_status AS ENUM ('adoptable', 'adopted', 'found');

CREATE TABLE IF NOT EXISTS sponsorship_emails
(
    id              UUID PRIMARY KEY NOT NULL,
    sponsorship_id  UUID REFERENCES sponsorships (id) ON DELETE RESTRICT,
    contact_email   TEXT             NOT NULL,
    adoption_status adoption_status  NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT (now() at time zone 'utc'),
    modified_at     TIMESTAMP WITH TIME ZONE DEFAULT (now() at time zone 'utc'),
    last_polled_at  TIMESTAMP WITH TIME ZONE
);

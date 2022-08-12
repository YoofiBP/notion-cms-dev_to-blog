create table post_metadata
(
    id        bigserial not null unique,
    notion_id text      not null,
    dev_to_id text      not null,
    primary key (id)
);
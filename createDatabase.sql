CREATE DATABASE socialnetwork
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'English_United States.1252'
    LC_CTYPE = 'English_United States.1252'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;
 \c socialnetwork
CREATE TABLE public.person
(
    username character varying(30) COLLATE pg_catalog."default",
    name character varying(30) COLLATE pg_catalog."default",
    type character varying(3) COLLATE pg_catalog."default",
    id character varying(30) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT person_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE public.person
    OWNER to postgres;

CREATE TABLE public.channel
(
    id integer NOT NULL,
    username character varying(60) COLLATE pg_catalog."default",
    name character varying(40) COLLATE pg_catalog."default",
    type character varying(3) COLLATE pg_catalog."default",
    channel_group boolean,
    lastmessageid integer,
    CONSTRAINT channel_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE public.channel
    OWNER to postgres;

CREATE TABLE public.person_channel
(
    person_id character varying(30) COLLATE pg_catalog."default" NOT NULL,
    channel_id integer NOT NULL,
    CONSTRAINT person_channel_pkey PRIMARY KEY (person_id, channel_id),
    CONSTRAINT channelid_fk FOREIGN KEY (channel_id)
        REFERENCES public.channel (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT fk_person_id FOREIGN KEY (person_id)
        REFERENCES public.person (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE public.person_channel
    OWNER to postgres;

CREATE SEQUENCE public.myseq_message
    INCREMENT 1
    START 3040
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

ALTER SEQUENCE public.myseq_message
    OWNER TO postgres;

CREATE TABLE public.message
(
    id integer NOT NULL DEFAULT nextval('myseq_message'::regclass),
    user_id character varying(30) COLLATE pg_catalog."default",
    channel_id integer,
    date timestamp with time zone,
    content text COLLATE pg_catalog."default",
    sentiment integer NOT NULL,
	stock character varying(10) COLLATE pg_catalog."default",
    image bytea,
	
    CONSTRAINT messages_pkey PRIMARY KEY (id),
    CONSTRAINT fk_channel FOREIGN KEY (channel_id)
        REFERENCES public.channel (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT fk_userid FOREIGN KEY (user_id)
        REFERENCES public.person (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE public.message
    OWNER to postgres;

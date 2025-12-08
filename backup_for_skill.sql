--
-- PostgreSQL database dump
--

-- Dumped from database version 14.19 (Homebrew)
-- Dumped by pg_dump version 17.5

-- Started on 2025-12-08 14:05:25 IST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 4 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: stalin_j
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO stalin_j;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 222 (class 1259 OID 80069)
-- Name: category_skill_templates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.category_skill_templates (
    id integer NOT NULL,
    category character varying NOT NULL,
    skill_id integer NOT NULL,
    is_required boolean NOT NULL,
    display_order integer
);


ALTER TABLE public.category_skill_templates OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 80068)
-- Name: category_skill_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.category_skill_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.category_skill_templates_id_seq OWNER TO postgres;

--
-- TOC entry 3973 (class 0 OID 0)
-- Dependencies: 221
-- Name: category_skill_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.category_skill_templates_id_seq OWNED BY public.category_skill_templates.id;


--
-- TOC entry 226 (class 1259 OID 80107)
-- Name: course_assignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.course_assignments (
    id integer NOT NULL,
    course_id integer NOT NULL,
    employee_id integer NOT NULL,
    assigned_by integer,
    assigned_at timestamp without time zone NOT NULL,
    due_date timestamp without time zone,
    status character varying(50) NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    certificate_url character varying,
    notes character varying
);


ALTER TABLE public.course_assignments OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 80106)
-- Name: course_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.course_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.course_assignments_id_seq OWNER TO postgres;

--
-- TOC entry 3976 (class 0 OID 0)
-- Dependencies: 225
-- Name: course_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.course_assignments_id_seq OWNED BY public.course_assignments.id;


--
-- TOC entry 224 (class 1259 OID 80087)
-- Name: courses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.courses (
    id integer NOT NULL,
    title character varying NOT NULL,
    description character varying,
    skill_id integer,
    external_url character varying,
    is_mandatory boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    created_by integer
);


ALTER TABLE public.courses OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 80086)
-- Name: courses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.courses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.courses_id_seq OWNER TO postgres;

--
-- TOC entry 3979 (class 0 OID 0)
-- Dependencies: 223
-- Name: courses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.courses_id_seq OWNED BY public.courses.id;


--
-- TOC entry 216 (class 1259 OID 80011)
-- Name: employee_skills; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.employee_skills (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    skill_id integer NOT NULL,
    rating character varying(50),
    initial_rating character varying(50),
    years_experience double precision,
    is_interested boolean NOT NULL,
    notes character varying,
    match_score double precision,
    needs_review boolean NOT NULL,
    is_custom boolean NOT NULL,
    learning_status character varying DEFAULT 'Not Started'::character varying NOT NULL,
    status_updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.employee_skills OWNER TO postgres;

--
-- TOC entry 215 (class 1259 OID 80010)
-- Name: employee_skills_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.employee_skills_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.employee_skills_id_seq OWNER TO postgres;

--
-- TOC entry 3982 (class 0 OID 0)
-- Dependencies: 215
-- Name: employee_skills_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.employee_skills_id_seq OWNED BY public.employee_skills.id;


--
-- TOC entry 232 (class 1259 OID 80227)
-- Name: employee_template_responses; Type: TABLE; Schema: public; Owner: skillboard
--

CREATE TABLE public.employee_template_responses (
    id integer NOT NULL,
    assignment_id integer NOT NULL,
    employee_category character varying NOT NULL,
    skill_id integer NOT NULL,
    employee_level character varying,
    years_experience double precision,
    notes character varying,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.employee_template_responses OWNER TO skillboard;

--
-- TOC entry 231 (class 1259 OID 80226)
-- Name: employee_template_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: skillboard
--

CREATE SEQUENCE public.employee_template_responses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.employee_template_responses_id_seq OWNER TO skillboard;

--
-- TOC entry 3984 (class 0 OID 0)
-- Dependencies: 231
-- Name: employee_template_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: skillboard
--

ALTER SEQUENCE public.employee_template_responses_id_seq OWNED BY public.employee_template_responses.id;


--
-- TOC entry 214 (class 1259 OID 79995)
-- Name: employees; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.employees (
    id integer NOT NULL,
    employee_id character varying NOT NULL,
    name character varying NOT NULL,
    first_name character varying,
    last_name character varying,
    company_email character varying,
    department character varying,
    role character varying,
    team character varying,
    band character varying,
    category character varying
);


ALTER TABLE public.employees OWNER TO postgres;

--
-- TOC entry 213 (class 1259 OID 79994)
-- Name: employees_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.employees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.employees_id_seq OWNER TO postgres;

--
-- TOC entry 3986 (class 0 OID 0)
-- Dependencies: 213
-- Name: employees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.employees_id_seq OWNED BY public.employees.id;


--
-- TOC entry 220 (class 1259 OID 80051)
-- Name: role_requirements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.role_requirements (
    id integer NOT NULL,
    band character varying NOT NULL,
    skill_id integer NOT NULL,
    required_rating character varying(50) NOT NULL,
    is_required boolean NOT NULL
);


ALTER TABLE public.role_requirements OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 80050)
-- Name: role_requirements_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.role_requirements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.role_requirements_id_seq OWNER TO postgres;

--
-- TOC entry 3989 (class 0 OID 0)
-- Dependencies: 219
-- Name: role_requirements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.role_requirements_id_seq OWNED BY public.role_requirements.id;


--
-- TOC entry 234 (class 1259 OID 80249)
-- Name: skill_gap_results; Type: TABLE; Schema: public; Owner: skillboard
--

CREATE TABLE public.skill_gap_results (
    id integer NOT NULL,
    assignment_id integer NOT NULL,
    skill_id integer NOT NULL,
    required_level character varying NOT NULL,
    employee_level character varying,
    gap_status character varying NOT NULL,
    gap_value integer NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.skill_gap_results OWNER TO skillboard;

--
-- TOC entry 233 (class 1259 OID 80248)
-- Name: skill_gap_results_id_seq; Type: SEQUENCE; Schema: public; Owner: skillboard
--

CREATE SEQUENCE public.skill_gap_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.skill_gap_results_id_seq OWNER TO skillboard;

--
-- TOC entry 3991 (class 0 OID 0)
-- Dependencies: 233
-- Name: skill_gap_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: skillboard
--

ALTER SEQUENCE public.skill_gap_results_id_seq OWNED BY public.skill_gap_results.id;


--
-- TOC entry 228 (class 1259 OID 80141)
-- Name: skill_templates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.skill_templates (
    id integer NOT NULL,
    template_name character varying NOT NULL,
    file_name character varying NOT NULL,
    content character varying NOT NULL,
    created_at timestamp without time zone NOT NULL,
    uploaded_by integer
);


ALTER TABLE public.skill_templates OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 80140)
-- Name: skill_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.skill_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.skill_templates_id_seq OWNER TO postgres;

--
-- TOC entry 3993 (class 0 OID 0)
-- Dependencies: 227
-- Name: skill_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.skill_templates_id_seq OWNED BY public.skill_templates.id;


--
-- TOC entry 210 (class 1259 OID 79971)
-- Name: skills; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.skills (
    id integer NOT NULL,
    name character varying NOT NULL,
    description character varying,
    category character varying
);


ALTER TABLE public.skills OWNER TO postgres;

--
-- TOC entry 209 (class 1259 OID 79970)
-- Name: skills_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.skills_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.skills_id_seq OWNER TO postgres;

--
-- TOC entry 3996 (class 0 OID 0)
-- Dependencies: 209
-- Name: skills_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.skills_id_seq OWNED BY public.skills.id;


--
-- TOC entry 218 (class 1259 OID 80033)
-- Name: team_skill_templates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_skill_templates (
    id integer NOT NULL,
    team character varying NOT NULL,
    skill_id integer NOT NULL,
    is_required boolean NOT NULL,
    display_order integer
);


ALTER TABLE public.team_skill_templates OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 80032)
-- Name: team_skill_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.team_skill_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_skill_templates_id_seq OWNER TO postgres;

--
-- TOC entry 3999 (class 0 OID 0)
-- Dependencies: 217
-- Name: team_skill_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.team_skill_templates_id_seq OWNED BY public.team_skill_templates.id;


--
-- TOC entry 230 (class 1259 OID 80189)
-- Name: template_assignments; Type: TABLE; Schema: public; Owner: skillboard
--

CREATE TABLE public.template_assignments (
    id integer NOT NULL,
    template_id integer NOT NULL,
    employee_id integer NOT NULL,
    assigned_by integer,
    assigned_at timestamp without time zone NOT NULL,
    status character varying NOT NULL,
    category_hr character varying
);


ALTER TABLE public.template_assignments OWNER TO skillboard;

--
-- TOC entry 229 (class 1259 OID 80188)
-- Name: template_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: skillboard
--

CREATE SEQUENCE public.template_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.template_assignments_id_seq OWNER TO skillboard;

--
-- TOC entry 4001 (class 0 OID 0)
-- Dependencies: 229
-- Name: template_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: skillboard
--

ALTER SEQUENCE public.template_assignments_id_seq OWNED BY public.template_assignments.id;


--
-- TOC entry 212 (class 1259 OID 79983)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    employee_id character varying,
    email character varying NOT NULL,
    password_hash character varying NOT NULL,
    is_active boolean NOT NULL,
    is_admin boolean NOT NULL,
    must_change_password boolean NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 211 (class 1259 OID 79982)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- TOC entry 4003 (class 0 OID 0)
-- Dependencies: 211
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 3703 (class 2604 OID 80072)
-- Name: category_skill_templates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_skill_templates ALTER COLUMN id SET DEFAULT nextval('public.category_skill_templates_id_seq'::regclass);


--
-- TOC entry 3705 (class 2604 OID 80110)
-- Name: course_assignments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_assignments ALTER COLUMN id SET DEFAULT nextval('public.course_assignments_id_seq'::regclass);


--
-- TOC entry 3704 (class 2604 OID 80090)
-- Name: courses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses ALTER COLUMN id SET DEFAULT nextval('public.courses_id_seq'::regclass);


--
-- TOC entry 3698 (class 2604 OID 80014)
-- Name: employee_skills id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_skills ALTER COLUMN id SET DEFAULT nextval('public.employee_skills_id_seq'::regclass);


--
-- TOC entry 3708 (class 2604 OID 80230)
-- Name: employee_template_responses id; Type: DEFAULT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.employee_template_responses ALTER COLUMN id SET DEFAULT nextval('public.employee_template_responses_id_seq'::regclass);


--
-- TOC entry 3697 (class 2604 OID 79998)
-- Name: employees id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employees ALTER COLUMN id SET DEFAULT nextval('public.employees_id_seq'::regclass);


--
-- TOC entry 3702 (class 2604 OID 80054)
-- Name: role_requirements id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_requirements ALTER COLUMN id SET DEFAULT nextval('public.role_requirements_id_seq'::regclass);


--
-- TOC entry 3709 (class 2604 OID 80252)
-- Name: skill_gap_results id; Type: DEFAULT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.skill_gap_results ALTER COLUMN id SET DEFAULT nextval('public.skill_gap_results_id_seq'::regclass);


--
-- TOC entry 3706 (class 2604 OID 80144)
-- Name: skill_templates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.skill_templates ALTER COLUMN id SET DEFAULT nextval('public.skill_templates_id_seq'::regclass);


--
-- TOC entry 3695 (class 2604 OID 79974)
-- Name: skills id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.skills ALTER COLUMN id SET DEFAULT nextval('public.skills_id_seq'::regclass);


--
-- TOC entry 3701 (class 2604 OID 80036)
-- Name: team_skill_templates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_skill_templates ALTER COLUMN id SET DEFAULT nextval('public.team_skill_templates_id_seq'::regclass);


--
-- TOC entry 3707 (class 2604 OID 80192)
-- Name: template_assignments id; Type: DEFAULT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.template_assignments ALTER COLUMN id SET DEFAULT nextval('public.template_assignments_id_seq'::regclass);


--
-- TOC entry 3696 (class 2604 OID 79986)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 3953 (class 0 OID 80069)
-- Dependencies: 222
-- Data for Name: category_skill_templates; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.category_skill_templates (id, category, skill_id, is_required, display_order) FROM stdin;
\.


--
-- TOC entry 3957 (class 0 OID 80107)
-- Dependencies: 226
-- Data for Name: course_assignments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.course_assignments (id, course_id, employee_id, assigned_by, assigned_at, due_date, status, started_at, completed_at, certificate_url, notes) FROM stdin;
1	1	6	3	2025-12-08 07:38:17.434695	\N	NOT_STARTED	\N	\N	\N	\N
2	1	7	3	2025-12-08 07:38:17.434703	\N	NOT_STARTED	\N	\N	\N	\N
3	1	8	3	2025-12-08 07:38:17.434703	\N	NOT_STARTED	\N	\N	\N	\N
4	1	9	3	2025-12-08 07:38:17.434704	\N	NOT_STARTED	\N	\N	\N	\N
5	1	10	3	2025-12-08 07:38:17.434705	\N	NOT_STARTED	\N	\N	\N	\N
6	1	1	3	2025-12-08 07:38:17.434705	\N	NOT_STARTED	\N	\N	\N	\N
7	2	6	3	2025-12-08 07:38:17.434706	\N	NOT_STARTED	\N	\N	\N	\N
8	2	7	3	2025-12-08 07:38:17.434707	\N	NOT_STARTED	\N	\N	\N	\N
9	2	8	3	2025-12-08 07:38:17.434707	\N	NOT_STARTED	\N	\N	\N	\N
10	2	9	3	2025-12-08 07:38:17.434708	\N	NOT_STARTED	\N	\N	\N	\N
11	2	10	3	2025-12-08 07:38:17.434709	\N	NOT_STARTED	\N	\N	\N	\N
12	2	1	3	2025-12-08 07:38:17.434709	\N	NOT_STARTED	\N	\N	\N	\N
13	5	6	3	2025-12-08 07:43:24.551434	\N	Not Started	\N	\N	\N	\N
14	5	7	3	2025-12-08 07:43:24.551434	\N	Not Started	\N	\N	\N	\N
15	5	8	3	2025-12-08 07:43:24.551434	\N	Not Started	\N	\N	\N	\N
16	5	9	3	2025-12-08 07:43:24.551434	\N	Not Started	\N	\N	\N	\N
17	5	10	3	2025-12-08 07:43:24.551434	\N	Not Started	\N	\N	\N	\N
18	5	1	3	2025-12-08 07:43:24.551434	\N	Not Started	\N	\N	\N	\N
19	6	6	3	2025-12-08 07:43:24.55678	\N	Not Started	\N	\N	\N	\N
20	6	7	3	2025-12-08 07:43:24.55678	\N	Not Started	\N	\N	\N	\N
21	6	8	3	2025-12-08 07:43:24.55678	\N	Not Started	\N	\N	\N	\N
22	6	9	3	2025-12-08 07:43:24.55678	\N	Not Started	\N	\N	\N	\N
23	6	10	3	2025-12-08 07:43:24.55678	\N	Not Started	\N	\N	\N	\N
24	6	1	3	2025-12-08 07:43:24.55678	\N	Not Started	\N	\N	\N	\N
\.


--
-- TOC entry 3955 (class 0 OID 80087)
-- Dependencies: 224
-- Data for Name: courses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.courses (id, title, description, skill_id, external_url, is_mandatory, created_at, created_by) FROM stdin;
1	Google Cloud Associate Cloud Engineer Certification	Prepare for the Google Cloud Associate Cloud Engineer certification. Learn to deploy applications, monitor operations, and manage enterprise solutions.	\N	https://www.cloudskillsboost.google/paths/11	t	2025-12-08 07:38:17.091033	3
2	AWS Certified Solutions Architect - Associate	Master AWS services and architecture. Learn to design distributed systems on AWS.	\N	https://aws.amazon.com/certification/certified-solutions-architect-associate/	t	2025-12-08 07:38:17.260861	3
3	Python for Data Science - Coursera	Learn Python programming for data science and machine learning applications.	\N	https://www.coursera.org/specializations/python-data-science	f	2025-12-08 07:38:17.262306	3
4	Docker and Kubernetes Complete Guide	Master containerization with Docker and orchestration with Kubernetes.	\N	https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/	f	2025-12-08 07:38:17.263332	3
5	Google Cloud Associate Cloud Engineer Certification	Prepare for the Google Cloud Associate Cloud Engineer certification. Learn to deploy applications, monitor operations, and manage enterprise solutions.	\N	https://www.cloudskillsboost.google/paths/11	t	2025-12-08 07:42:58.150343	3
6	AWS Certified Solutions Architect - Associate	Master AWS services and architecture. Learn to design distributed systems on AWS.	\N	https://aws.amazon.com/certification/certified-solutions-architect-associate/	t	2025-12-08 07:43:09.369113	3
\.


--
-- TOC entry 3947 (class 0 OID 80011)
-- Dependencies: 216
-- Data for Name: employee_skills; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.employee_skills (id, employee_id, skill_id, rating, initial_rating, years_experience, is_interested, notes, match_score, needs_review, is_custom, learning_status, status_updated_at) FROM stdin;
1	6	1	EXPERT	EXPERT	8	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446915
2	6	2	INTERMEDIATE	INTERMEDIATE	7	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446922
3	6	3	\N	\N	0	t	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446923
4	6	4	\N	\N	0	t	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446924
5	7	1	EXPERT	EXPERT	2	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446925
6	7	6	INTERMEDIATE	INTERMEDIATE	1	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446926
7	7	8	ADVANCED	ADVANCED	4	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446927
8	7	7	\N	\N	0	t	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446928
9	8	10	EXPERT	EXPERT	1	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446928
10	8	13	ADVANCED	ADVANCED	6	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446929
11	8	11	INTERMEDIATE	INTERMEDIATE	10	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.44693
12	8	12	\N	\N	0	t	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446931
13	9	14	EXPERT	EXPERT	8	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446931
14	9	15	ADVANCED	ADVANCED	10	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446932
15	9	17	INTERMEDIATE	INTERMEDIATE	7	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446933
16	9	16	\N	\N	0	t	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446934
17	10	18	EXPERT	EXPERT	4	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446934
18	10	8	ADVANCED	ADVANCED	2	f	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446935
20	10	12	\N	\N	0	t	Auto-assigned by script	\N	f	f	Not Started	2025-12-07 05:01:10.446936
22	1	2	BEGINNER	BEGINNER	\N	f	\N	\N	f	t	Not Started	2025-12-07 12:05:02.203278
23	1	4	\N	\N	\N	t	\N	\N	f	t	Not Started	2025-12-07 12:05:22.027883
21	1	1	ADVANCED	EXPERT	\N	f	\N	\N	f	t	Not Started	2025-12-07 12:04:37.906757
19	10	19	BEGINNER	BEGINNER	8	f	{"plan":"Auto-assigned by script","targetDate":""}	\N	f	f	Not Started	2025-12-08 08:26:40.15863
\.


--
-- TOC entry 3963 (class 0 OID 80227)
-- Dependencies: 232
-- Data for Name: employee_template_responses; Type: TABLE DATA; Schema: public; Owner: skillboard
--

COPY public.employee_template_responses (id, assignment_id, employee_category, skill_id, employee_level, years_experience, notes, created_at) FROM stdin;
205	7	General	21	Beginner	0	Test 1	2025-12-07 14:28:37.06698
206	7	General	41	Intermediate	0	Test 2	2025-12-07 14:28:37.066984
214	5	General	1	Beginner	0	Initial assessment	2025-11-07 20:11:45.773698
215	5	General	2	Developing	0	Initial assessment	2025-11-07 20:11:45.774135
216	5	General	3	Beginner	0	Initial assessment	2025-11-07 20:11:45.774527
217	5	General	1	Intermediate	0	After training and practice!	2025-12-07 20:11:45.779099
218	5	General	2	Advanced	0	After training and practice!	2025-12-07 20:11:45.779456
219	5	General	3	Expert	0	After training and practice!	2025-12-07 20:11:45.779789
220	6	General	42	Beginner	0		2025-12-07 15:02:55.19307
221	6	General	43	Beginner	0		2025-12-07 15:02:55.213549
222	6	General	44	Developing	0		2025-12-07 15:02:55.215231
223	6	General	45	Intermediate	0		2025-12-07 15:02:55.216194
224	6	General	46	Intermediate	0		2025-12-07 15:02:55.217065
225	6	General	47	Beginner	0		2025-12-07 15:02:55.218144
226	6	General	48	Intermediate	0		2025-12-07 15:02:55.219837
227	6	General	49	Beginner	0		2025-12-07 15:02:55.220688
228	6	General	50	Developing	0		2025-12-07 15:02:55.221607
229	6	General	51	Developing	0		2025-12-07 15:02:55.222584
230	6	General	52	Developing	0		2025-12-07 15:02:55.224283
231	6	General	53	Developing	0		2025-12-07 15:02:55.225482
232	6	General	54	Developing	0		2025-12-07 15:02:55.226408
233	6	General	55	Intermediate	0		2025-12-07 15:02:55.228522
234	6	General	56	Developing	0		2025-12-07 15:02:55.229396
235	6	General	57	Developing	0		2025-12-07 15:02:55.230344
236	6	General	58	Developing	0		2025-12-07 15:02:55.232647
237	6	General	59	Beginner	0		2025-12-07 15:02:55.233669
238	6	General	60	Beginner	0		2025-12-07 15:02:55.235094
239	6	General	61	Developing	0		2025-12-07 15:02:55.236278
240	6	General	62	Developing	0		2025-12-07 15:02:55.237126
241	6	General	63	Beginner	0		2025-12-07 15:02:55.238061
242	6	General	64	Developing	0		2025-12-07 15:02:55.238927
243	6	General	65	Developing	0		2025-12-07 15:02:55.239775
244	6	General	66	Beginner	0		2025-12-07 15:02:55.241992
245	6	General	67	Developing	0		2025-12-07 15:02:55.243295
246	6	General	68	Intermediate	0		2025-12-07 15:02:55.247865
247	9	General	42	Beginner	0		2025-12-08 05:31:57.316996
248	9	General	43	Developing	0		2025-12-08 05:31:57.317002
249	9	General	44	Developing	0		2025-12-08 05:31:57.317004
250	9	General	45	Beginner	0		2025-12-08 05:31:57.317005
251	9	General	46	Beginner	0		2025-12-08 05:31:57.317006
252	9	General	47	Beginner	0		2025-12-08 05:31:57.317008
253	9	General	48	Beginner	0		2025-12-08 05:31:57.317009
254	9	General	49	Beginner	0		2025-12-08 05:31:57.31701
255	9	General	50	Beginner	0		2025-12-08 05:31:57.317011
256	9	General	51	Beginner	0		2025-12-08 05:31:57.317012
257	9	General	52	Beginner	0		2025-12-08 05:31:57.317013
258	9	General	53	Developing	0		2025-12-08 05:31:57.317014
259	9	General	54	Beginner	0		2025-12-08 05:31:57.317015
260	9	General	55	Beginner	0		2025-12-08 05:31:57.317016
261	9	General	56	Beginner	0		2025-12-08 05:31:57.317017
262	9	General	57	Beginner	0		2025-12-08 05:31:57.317019
263	9	General	58	Beginner	0		2025-12-08 05:31:57.31702
264	9	General	59	Beginner	0		2025-12-08 05:31:57.317021
265	9	General	60	Beginner	0		2025-12-08 05:31:57.317022
266	9	General	61	Developing	0		2025-12-08 05:31:57.317023
267	9	General	62	Beginner	0		2025-12-08 05:31:57.317024
268	9	General	63	Beginner	0		2025-12-08 05:31:57.317025
269	9	General	64	Beginner	0		2025-12-08 05:31:57.317026
270	9	General	65	Beginner	0		2025-12-08 05:31:57.317027
271	9	General	66	Beginner	0		2025-12-08 05:31:57.317028
272	9	General	67	Beginner	0		2025-12-08 05:31:57.317029
273	9	General	68	Beginner	0		2025-12-08 05:31:57.31703
274	10	General	21	Beginner	0		2025-12-08 05:44:41.76978
275	10	General	41	Beginner	0		2025-12-08 05:44:41.769789
276	10	General	70	Beginner	0		2025-12-08 05:44:41.780802
277	10	General	71	Beginner	0		2025-12-08 05:44:41.782189
278	10	General	72	Beginner	0		2025-12-08 05:44:41.783663
279	10	General	73	Beginner	0		2025-12-08 05:44:41.785192
280	10	General	74	Beginner	0		2025-12-08 05:44:41.786606
281	10	General	75	Beginner	0		2025-12-08 05:44:41.787829
282	10	General	76	Developing	0		2025-12-08 05:44:41.789173
283	10	General	77	Beginner	0		2025-12-08 05:44:41.790583
284	10	General	78	Beginner	0		2025-12-08 05:44:41.791907
285	10	General	79	Beginner	0		2025-12-08 05:44:41.793078
286	10	General	80	Beginner	0		2025-12-08 05:44:41.794871
287	10	General	81	Beginner	0		2025-12-08 05:44:41.795791
288	10	General	82	Beginner	0		2025-12-08 05:44:41.796676
289	10	General	83	Beginner	0		2025-12-08 05:44:41.797468
290	10	General	84	Beginner	0		2025-12-08 05:44:41.798306
291	10	General	85	Beginner	0		2025-12-08 05:44:41.800031
292	10	General	85	Beginner	0		2025-12-08 05:44:41.800033
293	10	General	86	Beginner	0		2025-12-08 05:44:41.802803
294	10	General	86	Beginner	0		2025-12-08 05:44:41.802805
295	10	General	86	Developing	0		2025-12-08 05:44:41.802806
296	10	General	87	Beginner	0		2025-12-08 05:44:41.804936
297	10	General	88	Beginner	0		2025-12-08 05:44:41.806306
298	10	General	89	Beginner	0		2025-12-08 05:44:41.807616
299	10	General	90	Beginner	0		2025-12-08 05:44:41.808824
300	10	General	91	Beginner	0		2025-12-08 05:44:41.809995
301	10	General	92	Beginner	0		2025-12-08 05:44:41.81119
302	10	General	93	Developing	0		2025-12-08 05:44:41.812351
303	10	General	94	Beginner	0		2025-12-08 05:44:41.813089
304	10	General	95	Beginner	0		2025-12-08 05:44:41.814813
305	10	General	58	Beginner	0		2025-12-08 05:44:41.814816
306	10	General	96	Beginner	0		2025-12-08 05:44:41.816371
307	10	General	97	Beginner	0		2025-12-08 05:44:41.81803
308	10	General	98	Beginner	0		2025-12-08 05:44:41.819294
309	10	General	99	Beginner	0		2025-12-08 05:44:41.820504
310	10	General	100	Developing	0		2025-12-08 05:44:41.822204
311	10	General	64	Beginner	0		2025-12-08 05:44:41.822206
312	10	General	101	Beginner	0		2025-12-08 05:44:41.823984
313	10	General	102	Beginner	0		2025-12-08 05:44:41.82527
314	10	General	103	Beginner	0		2025-12-08 05:44:41.826458
315	10	General	104	Beginner	0		2025-12-08 05:44:41.828218
345	11	General	105	Beginner	0		2025-12-08 05:49:51.901778
346	11	General	106	Developing	0		2025-12-08 05:49:51.901787
347	11	General	107	Beginner	0		2025-12-08 05:49:51.90179
348	11	General	108	Beginner	0		2025-12-08 05:49:51.901792
349	11	General	109	Beginner	0		2025-12-08 05:49:51.901795
350	11	General	110	Developing	0		2025-12-08 05:49:51.901797
351	11	General	111	Intermediate	0		2025-12-08 05:49:51.9018
352	11	General	112	Beginner	0		2025-12-08 05:49:51.901802
353	11	General	113	Beginner	0		2025-12-08 05:49:51.901804
354	11	General	114	Beginner	0		2025-12-08 05:49:51.901806
355	11	General	115	Beginner	0		2025-12-08 05:49:51.901809
356	11	General	116	Beginner	0		2025-12-08 05:49:51.901811
357	11	General	117	Beginner	0		2025-12-08 05:49:51.901813
358	11	General	118	Beginner	0		2025-12-08 05:49:51.901815
359	11	General	119	Beginner	0		2025-12-08 05:49:51.901817
360	11	General	120	Beginner	0		2025-12-08 05:49:51.90182
361	11	General	121	Developing	0		2025-12-08 05:49:51.901822
362	11	General	58	Beginner	0		2025-12-08 05:49:51.901824
363	11	General	122	Beginner	0		2025-12-08 05:49:51.901826
364	11	General	123	Beginner	0		2025-12-08 05:49:51.901828
365	11	General	124	Developing	0		2025-12-08 05:49:51.901831
366	11	General	125	Developing	0		2025-12-08 05:49:51.901833
367	11	General	126	Developing	0		2025-12-08 05:49:51.901835
368	11	General	64	Beginner	0		2025-12-08 05:49:51.901837
369	11	General	127	Beginner	0		2025-12-08 05:49:51.901839
370	11	General	128	Developing	0		2025-12-08 05:49:51.901841
371	11	General	129	Beginner	0		2025-12-08 05:49:51.901844
372	11	General	130	Beginner	0		2025-12-08 05:49:51.901846
373	11	General	131	Beginner	0		2025-12-08 05:49:51.901848
374	12	General	132	Beginner	0		2025-12-08 06:00:15.578236
375	12	General	133	Beginner	0		2025-12-08 06:00:15.58632
376	12	General	134	Beginner	0		2025-12-08 06:00:15.587971
377	12	General	135	Beginner	0		2025-12-08 06:00:15.589575
378	12	General	136	Developing	0		2025-12-08 06:00:15.591294
379	12	General	137	Developing	0		2025-12-08 06:00:15.592392
380	12	General	138	Developing	0		2025-12-08 06:00:15.593641
381	12	General	139	Beginner	0		2025-12-08 06:00:15.595035
382	12	General	140	Beginner	0		2025-12-08 06:00:15.596377
383	12	General	141	Beginner	0		2025-12-08 06:00:15.597726
384	12	General	142	Beginner	0		2025-12-08 06:00:15.598956
385	12	General	143	Beginner	0		2025-12-08 06:00:15.600861
386	12	General	54	Beginner	0		2025-12-08 06:00:15.600863
387	12	General	144	Developing	0		2025-12-08 06:00:15.604142
388	12	General	145	Developing	0		2025-12-08 06:00:15.605482
389	12	General	146	Beginner	0		2025-12-08 06:00:15.607581
390	12	General	58	Developing	0		2025-12-08 06:00:15.607584
391	12	General	147	Developing	0		2025-12-08 06:00:15.609343
392	12	General	148	Beginner	0		2025-12-08 06:00:15.61107
393	12	General	63	Beginner	0		2025-12-08 06:00:15.611072
394	12	General	149	Beginner	0		2025-12-08 06:00:15.613161
395	12	General	64	Developing	0		2025-12-08 06:00:15.613164
396	12	General	150	Beginner	0		2025-12-08 06:00:15.614831
397	12	General	151	Beginner	0		2025-12-08 06:00:15.615973
398	12	General	152	Developing	0		2025-12-08 06:00:15.617291
399	12	General	153	Beginner	0		2025-12-08 06:00:15.618645
400	12	General	154	Developing	0		2025-12-08 06:00:15.620461
\.


--
-- TOC entry 3945 (class 0 OID 79995)
-- Dependencies: 214
-- Data for Name: employees; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.employees (id, employee_id, name, first_name, last_name, company_email, department, role, team, band, category) FROM stdin;
6	EMP001	Alice Engineer	\N	\N	alice@skillboard.com	Engineering	Software Engineer	Technical Delivery	B	Employee
7	EMP002	Bob Lead	\N	\N	bob@skillboard.com	Engineering	Team Lead	Technical Delivery	C	Employee
8	EMP003	Charlie HR	\N	\N	charlie@skillboard.com	HR	HR Manager	Corporate Functions - PC	C	Employee
9	EMP004	David Sales	\N	\N	david@skillboard.com	Sales	Sales Executive	Consulting	A	Employee
10	EMP005	Eve Product	\N	\N	eve@skillboard.com	Product	Product Manager	Consulting	B	Employee
1	E001	stalin J	stalin	J	stalinj4747@gmail.com	\N	Consultant	\N	A	\N
\.


--
-- TOC entry 3951 (class 0 OID 80051)
-- Dependencies: 220
-- Data for Name: role_requirements; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.role_requirements (id, band, skill_id, required_rating, is_required) FROM stdin;
\.


--
-- TOC entry 3965 (class 0 OID 80249)
-- Dependencies: 234
-- Data for Name: skill_gap_results; Type: TABLE DATA; Schema: public; Owner: skillboard
--

COPY public.skill_gap_results (id, assignment_id, skill_id, required_level, employee_level, gap_status, gap_value, created_at) FROM stdin;
1	5	1	Intermediate	Beginner	Gap	-2	2025-12-07 13:01:29.513007
2	5	2	Intermediate	Intermediate	Met	0	2025-12-07 13:01:29.513009
3	5	3	Intermediate	Advanced	Exceeded	1	2025-12-07 13:01:29.51301
4	5	4	Intermediate	Intermediate	Met	0	2025-12-07 13:01:29.51301
5	5	5	Intermediate	Developing	Gap	-1	2025-12-07 13:01:29.513011
167	12	132	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628573
168	12	133	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628576
169	12	134	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628578
170	12	135	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628579
171	12	136	Intermediate	Developing	Gap	-1	2025-12-08 06:00:15.62858
11	7	21	Intermediate	Beginner	Gap	-2	2025-12-07 14:28:37.075362
12	7	41	Intermediate	Intermediate	Met	0	2025-12-07 14:28:37.075364
172	12	137	Intermediate	Developing	Gap	-1	2025-12-08 06:00:15.628582
173	12	138	Intermediate	Developing	Gap	-1	2025-12-08 06:00:15.628583
174	12	139	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628584
175	12	140	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628586
176	12	141	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628587
177	12	142	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628588
178	12	143	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.62859
179	12	54	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628591
180	12	144	Intermediate	Developing	Gap	-1	2025-12-08 06:00:15.628592
181	12	145	Intermediate	Developing	Gap	-1	2025-12-08 06:00:15.628594
182	12	146	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628595
183	12	58	Intermediate	Developing	Gap	-1	2025-12-08 06:00:15.628596
184	12	147	Intermediate	Developing	Gap	-1	2025-12-08 06:00:15.628597
185	12	148	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628599
186	12	63	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.6286
187	12	149	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628601
188	12	64	Intermediate	Developing	Gap	-1	2025-12-08 06:00:15.628603
189	12	150	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628604
190	12	151	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628605
191	12	152	Intermediate	Developing	Gap	-1	2025-12-08 06:00:15.628607
192	12	153	Intermediate	Beginner	Gap	-2	2025-12-08 06:00:15.628608
193	12	154	Intermediate	Developing	Gap	-1	2025-12-08 06:00:15.628609
\.


--
-- TOC entry 3959 (class 0 OID 80141)
-- Dependencies: 228
-- Data for Name: skill_templates; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.skill_templates (id, template_name, file_name, content, created_at, uploaded_by) FROM stdin;
52	Skill Management - Technical_Delivery_Pathway	skill .33.xlsx	[["", "", "", "", "", ""], ["Skill", "A", "B", "C", "L1", "L2"], [" Core Technical Skills - Select those that apply", "", "", "", "", ""], ["1. Solution Design & Architecture", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Systems design and integration", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Technical requirements analysis", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Cloud architecture (AWS, Azure, GCP)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["API design and microservices", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["2. Software Engineering / Development", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Programming languages (e.g. Python, Java, C#, JavaScript)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Version control (Git)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Test-driven development (TDD)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Secure coding practices", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["3. DevOps & Automation", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["CI/CD pipelines (Jenkins, GitHub Actions, Azure DevOps)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Infrastructure as Code (Terraform, Ansible)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Containerisation (Docker, Kubernetes)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Monitoring & logging (Prometheus, ELK stack)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["4. Data & Analytics", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Data modelling and ETL pipelines", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["SQL and NoSQL databases", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Data visualisation (Power BI, Tableau)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Machine learning (optional depending on role)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["", "", "", "", "", ""], ["Delivery & Collaboration Skills", "", "", "", "", ""], ["1. Agile & Delivery Practices", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Scrum, Kanban, SAFe", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["User story writing and backlog grooming", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Sprint planning and retrospectives", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Technical documentation", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["2. Stakeholder Engagement", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Translating technical concepts for non-technical audiences", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Working with product owners and business analysts", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Managing technical risks and dependencies", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["3. Quality Assurance", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Unit, integration, and system testing", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Performance and security testing", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Code reviews and peer feedback", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Tools & Platforms", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["IDEs (VS Code, IntelliJ)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Cloud platforms (AWS, Azure, GCP)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Collaboration tools (Confluence, Jira, Teams)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Source control (GitHub, GitLab, Bitbucket)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], [" Certifications (Role-Dependent)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["AWS / Azure / GCP certifications", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Certified Kubernetes Administrator (CKA)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Microsoft Certified: DevOps Engineer", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["TOGAF (for architecture roles)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["ISTQB (for QA roles)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["", "", "", "", "", ""], ["Techncial Delivery Practise - add the practise you work within", "", "", "", "", ""], ["Digital & Engineering Services", "", "", "", "", ""], ["Digital transformation strategy", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Agile delivery and DevOps", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Cloud-native development", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["API integration and microservices", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["UX/UI design principles", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Engineering", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Systems engineering and design", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["CAD tools and modelling", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Electrical and mechanical engineering principles", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Compliance with industry standards", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Project lifecycle management", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Data, Cloud & AI", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Data engineering (ETL, pipelines)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Cloud architecture (AWS, Azure, GCP)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Machine learning and AI frameworks", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Data governance and security", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Big data technologies (Spark, Hadoop)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Cyber Security", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Threat modelling and risk assessment", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Network security and encryption", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Identity and access management", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Security compliance (ISO 27001, NIST)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Incident response and penetration testing", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Asset Intelligence", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["IoT and sensor integration", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Predictive maintenance", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Asset lifecycle management", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Data analytics for asset performance", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Digital twin technology", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Strategic Programmes", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Portfolio and programme management", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Benefits realisation", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Governance frameworks (MSP, PRINCE2)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Stakeholder engagement", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Change management", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["GCC (Global Capability Centres)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Shared services management", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Process optimisation", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Knowledge management", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Automation and RPA", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Governance and compliance", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Enterprise Apps", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["ERP systems (SAP, Oracle)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["CRM platforms (Salesforce, Dynamics)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Integration and middleware", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Application lifecycle management", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Security and compliance for enterprise apps", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Power Design & Engineering", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Electrical system design", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Grid integration", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Power distribution and transmission", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Renewable energy integration", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Compliance with energy standards", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Renewables & Advisory", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Renewable energy technologies (solar, wind)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Feasibility studies and impact analysis", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Regulatory compliance", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Financial modelling for renewables", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Sustainability strategy", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Product Apps", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Mobile and web app development", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["API and microservices architecture", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["UX/UI design", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Performance optimisation", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Security and compliance", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""]]	2025-12-07 10:43:23.872219	3
53	Skill Management - Project_Programme_Man_Pathway	skill .33.xlsx	[["", "", "", "", "", ""], ["Skill", "A", "B", "C", "L1", "L2"], ["Core Delivery Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Project Planning & Scheduling: Work breakdown structures, Gantt charts, milestone tracking.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Risk & Issue Management: RAID logs, mitigation strategies, escalation processes.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Budgeting & Financial Control: Forecasting, cost tracking, variance analysis.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Resource Management: Capacity planning, team allocation, contractor oversight.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Governance & Reporting: Status reports, dashboards, steering packs.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Methodologies & Frameworks", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Agile Delivery: Scrum, Kanban, SAFe, Agile ceremonies.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Waterfall & Hybrid Models: Stage gates, documentation-heavy delivery.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Programme Management: MSP, portfolio alignment, benefits realisation.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Change Management: Stakeholder impact analysis, communications planning.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Stakeholder & Team Leadership", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Stakeholder Engagement: Mapping, influencing, conflict resolution.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Team Leadership: Coaching, performance management, motivation.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Client Relationship Management: Building trust, managing expectations.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Vendor Management: Contracts, SLAs, third-party coordination.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Tools & Technology", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Project Tools: MS Project, JIRA, Trello, Smartsheet.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Collaboration Tools: Teams, Miro, Confluence, SharePoint.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Reporting Tools: Power BI, Excel dashboards.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Documentation: RAID logs, delivery plans, governance packs.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Soft Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Communication & storytelling", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Problem-solving & decision-making", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Adaptability & resilience", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Strategic thinking", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Emotional intelligence", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Certifications (Typical)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Prince2 (Foundation & Practitioner)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["AgilePM / Scrum Master", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["MSP (Managing Successful Programmes)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["PMP (Project Management Professional)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["SAFe Agilist", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""]]	2025-12-07 10:43:23.872226	3
54	Skill Management - Corp_Functions_Pathways_IT	skill .33.xlsx	[["", "", "", "", "", ""], ["", "", "", "", "", ""], ["Skill", "A", "B", "C", "L1", "L2"], ["1. Core Technical Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Networking: TCP/IP, DNS, DHCP, VPN, firewalls.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Operating Systems: Windows, Linux, macOS administration.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Hardware & Infrastructure: Servers, storage, virtualization (VMware, Hyper-V).", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Cloud Computing: AWS, Azure, GCP fundamentals.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Cybersecurity Basics: Access control, encryption, threat detection.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["2. Software & Application Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Programming: Python, Java, C#, or scripting languages (PowerShell, Bash).", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Database Management: SQL, NoSQL, database design.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Application Support: ERP systems, CRM platforms.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["DevOps Practices: CI/CD pipelines, containerization (Docker, Kubernetes).", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["3. IT Service Management", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Incident & Problem Management: ITIL framework.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Change & Release Management: Governance and compliance.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Monitoring & Performance: Tools like Nagios, Splunk, Prometheus.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["4. Tools & Platforms", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Collaboration Tools: Microsoft Teams, SharePoint.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Version Control: GitHub, GitLab.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Virtualization & Cloud Tools: VMware, AWS Console, Azure Portal.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["5. Soft Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Troubleshooting and analytical thinking.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Communication and stakeholder engagement.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Time management and prioritization.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Adaptability and continuous learning.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["6. Certifications (Common)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["CompTIA A+, Network+, Security+", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Microsoft Certified: Azure Fundamentals", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["AWS Certified Solutions Architect", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Cisco CCNA", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["ITIL Foundation", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""]]	2025-12-07 10:43:23.872228	3
55	Skill Management - Corp_Functions_Pathways_Mkt_Com	skill .33.xlsx	[["", "", "", "", "", ""], ["", "", "", "", "", ""], ["Skill", "A", "B", "C", "L1", "L2"], ["1. Core Marketing Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Brand Management: Positioning, messaging, brand guidelines.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Campaign Planning & Execution: Multi-channel campaigns, timelines, KPIs.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Content Creation: Copywriting, storytelling, visual content.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Digital Marketing: SEO, SEM, social media strategy, email marketing.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Market Research & Analysis: Competitor analysis, audience segmentation.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["2. Communications Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Internal Communications: Employee engagement, newsletters, intranet updates.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["External Communications: Press releases, media relations, public statements.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Crisis Communication: Risk assessment, response planning.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Presentation & Public Speaking: Delivering clear and persuasive messages.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["3. Digital & Analytics", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Social Media Management: LinkedIn, Twitter, Instagram, TikTok strategies.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Analytics Tools: Google Analytics, social media insights, campaign reporting.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Marketing Automation: HubSpot, Marketo, Salesforce Marketing Cloud.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Content Management Systems (CMS): WordPress, Drupal.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["4. Creative & Design", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Graphic Design Basics: Canva, Adobe Creative Suite.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Video Production: Editing, scripting, storyboarding.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["UX Writing: Clear and user-friendly content for digital platforms.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["5. Soft Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Strong written and verbal communication.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Creativity and innovation.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Stakeholder management and collaboration.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Project management and time management.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Adaptability and problem-solving.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["6. Certifications (Common)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["CIM (Chartered Institute of Marketing)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Google Ads & Analytics Certifications", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["HubSpot Inbound Marketing", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["PRINCE2 (for campaign/project management)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["CIPR (Chartered Institute of Public Relations)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""]]	2025-12-07 10:43:23.872229	3
56	Skill Management - Corp_Functions_Pathways_Finance	skill .33.xlsx	[["", "", "", "", "", ""], ["", "", "", "", "", ""], ["Skill", "A", "B", "C", "L1", "L2"], ["1. Core Financial Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Financial Accounting: Preparing financial statements, balance sheets, income statements.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Management Accounting: Budgeting, forecasting, cost analysis.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Financial Reporting & Compliance: IFRS, GAAP standards, statutory reporting.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Taxation: Corporate tax, VAT, compliance with local regulations.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Audit & Assurance: Internal controls, risk assessment, compliance audits.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["2. Analytical & Strategic Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Financial Analysis: Ratio analysis, variance analysis, trend forecasting.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Investment & Treasury Management: Cash flow management, capital allocation.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Risk Management: Identifying financial risks, mitigation strategies.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Business Partnering: Supporting decision-making with financial insights.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["3. Technology & Tools", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["ERP Systems: SAP, Oracle Financials.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Accounting Software: QuickBooks, Xero.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Data Analysis Tools: Excel (advanced), Power BI, Tableau.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Automation & Digital Finance: RPA for finance processes.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["4. Regulatory & Compliance", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Knowledge of financial regulations and standards.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["GDPR and data privacy in financial reporting.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Anti-money laundering (AML) compliance.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["5. Soft Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Attention to detail and accuracy.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Communication and stakeholder engagement.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Problem-solving and critical thinking.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Time management and prioritization.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["6. Certifications (Common)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["ACCA (Association of Chartered Certified Accountants)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["CIMA (Chartered Institute of Management Accountants)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["ACA (Chartered Accountant)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["CFA (Chartered Financial Analyst)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["CPA (Certified Public Accountant)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""]]	2025-12-07 10:43:23.87223	3
57	Skill Management - skill 	skill .33.xlsx	[["", "", "", "", "", ""], ["", "", "", "", "", ""], ["Skill", "A", "B", "C", "L1", "L2"], ["1. Core Legal Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Legal Research & Analysis: Case law, statutes, regulatory frameworks.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Contract Drafting & Review: Agreements, terms & conditions, compliance clauses.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Regulatory Compliance: Industry-specific regulations, GDPR, anti-bribery laws.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Litigation Support: Preparing briefs, evidence management, liaising with counsel.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Risk Management: Identifying legal risks, mitigation strategies.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["2. Advisory & Negotiation", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Client Advisory: Providing clear, actionable legal advice.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Negotiation Skills: Settlements, contract terms, dispute resolution.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Policy Development: Creating internal governance and compliance policies.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["3. Specialised Legal Areas", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Corporate Law: M&A, company formation, governance.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Employment Law: Contracts, disputes, compliance.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Intellectual Property: Patents, trademarks, copyright.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Data Privacy & Cybersecurity Law: GDPR, data breach protocols.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["4. Technology & Tools", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Legal Tech Platforms: Document management systems, e-discovery tools.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Contract Lifecycle Management: Tools like DocuSign, ContractWorks.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Research Tools: LexisNexis, Westlaw.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["5. Soft Skills", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Attention to detail and accuracy.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Critical thinking and problem-solving.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Communication and influencing.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Confidentiality and ethical judgment.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Time management and prioritization.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["6. Certifications (Common)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Law degree (LLB/JD)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["LPC (Legal Practice Course) or equivalent", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["CILEX (Chartered Institute of Legal Executives)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Specialist certifications (e.g., GDPR Practitioner, Employment Law)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""]]	2025-12-07 10:43:23.872231	3
58	Skill Management - Corp_Functions_Pathways_P&C	skill .33.xlsx	[["", "", "", "", "", ""], ["", "", "", "", "", ""], ["Skill", "A", "B", "C", "L1", "L2"], ["1. Core HR Functional Skills", "", "", "", "", ""], ["Handling grievances", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Disciplinary Processes", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Conflict Resolution", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Job design", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Interviewing", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Onboarding", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Payroll", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Reward Strategies", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Benchmarking", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Creating Contracts", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Compliance & Record Keeping", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Appraisals", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Goal Setting", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Feedback Systems", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["2. Strategic HR Skills", "", "", "", "", ""], ["Workforce Planning: Forecasting talent needs", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Succession Planning", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Organisational Design & Development: Structuring teams", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Change Management", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Diversity, Equity & Inclusion (DEI): Policy development, cultural initiatives.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Diversity, Equity & Inclusion (DEI):  cultural initiatives.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Employee Engagement: Surveys", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Employee Engagement: engagement strategies", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Employee Engagement:  wellbeing programmes.", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["3. Compliance & Risk Management", "", "", "", "", ""], ["Employment law and regulations", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["GDPR and data privacy", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Health & safety compliance", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Policy development and auditing", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["4. HR Technology & Analytics", "", "", "", "", ""], ["HRIS systems (Dynamics)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Data analytics for HR metrics (turnover, engagement)", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Digital tools for recruitment and onboarding", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Automation in HR processes", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["5. Soft Skills", "", "", "", "", ""], ["Communication and influencing", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Coaching and mentoring", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Problem-solving and decision-making", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Emotional intelligence and empathy", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Negotiation and conflict resolution", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["6. Certifications (Common)", "", "", "", "", ""], ["CIPD Levels 3, 5, 7", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["SHRM-CP / SHRM-SCP", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Employment Law certifications", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["Coaching qualifications", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["", "Beginner", "Developing", "Intermediate", "Advanced", "Expert"], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""], ["", "", "", "", "", ""]]	2025-12-07 10:43:23.872232	3
\.


--
-- TOC entry 3941 (class 0 OID 79971)
-- Dependencies: 210
-- Data for Name: skills; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.skills (id, name, description, category) FROM stdin;
1	Python	Mastery of Python	General
2	React	Mastery of React	General
3	Docker	Mastery of Docker	General
4	AWS	Mastery of AWS	General
5	Kubernetes	Mastery of Kubernetes	General
6	Leadership	Mastery of Leadership	General
7	Project Management	Mastery of Project Management	General
8	Agile	Mastery of Agile	General
9	Scrum	Mastery of Scrum	General
10	Communication	Mastery of Communication	General
11	Excel	Mastery of Excel	General
12	Data Analysis	Mastery of Data Analysis	General
13	Recruiting	Mastery of Recruiting	General
14	Sales	Mastery of Sales	General
15	Negotiation	Mastery of Negotiation	General
16	Marketing	Mastery of Marketing	General
17	CRM	Mastery of CRM	General
18	Product Management	Mastery of Product Management	General
19	UX Design	Mastery of UX Design	General
20	Roadmapping	Mastery of Roadmapping	General
21	Handling grievances	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
41	Disciplinary Processes	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
42	Legal Research & Analysis	Skill from template: Skill Management - skill 	Template Skills
43	Contract Drafting & Review	Skill from template: Skill Management - skill 	Template Skills
44	Regulatory Compliance	Skill from template: Skill Management - skill 	Template Skills
45	Litigation Support	Skill from template: Skill Management - skill 	Template Skills
46	Risk Management	Skill from template: Skill Management - skill 	Template Skills
47	Client Advisory	Skill from template: Skill Management - skill 	Template Skills
48	Negotiation Skills	Skill from template: Skill Management - skill 	Template Skills
49	Policy Development	Skill from template: Skill Management - skill 	Template Skills
50	Corporate Law	Skill from template: Skill Management - skill 	Template Skills
51	Employment Law	Skill from template: Skill Management - skill 	Template Skills
52	Intellectual Property	Skill from template: Skill Management - skill 	Template Skills
53	Data Privacy & Cybersecurity Law	Skill from template: Skill Management - skill 	Template Skills
54	Template Skill 1018	Skill from template: Skill Management - skill 	Template Skills
55	Legal Tech Platforms	Skill from template: Skill Management - skill 	Template Skills
56	Contract Lifecycle Management	Skill from template: Skill Management - skill 	Template Skills
57	Research Tools	Skill from template: Skill Management - skill 	Template Skills
58	5. Soft Skills	Skill from template: Skill Management - skill 	Template Skills
59	Attention to detail and accuracy.	Skill from template: Skill Management - skill 	Template Skills
60	Critical thinking and problem-solving.	Skill from template: Skill Management - skill 	Template Skills
61	Communication and influencing.	Skill from template: Skill Management - skill 	Template Skills
62	Confidentiality and ethical judgment.	Skill from template: Skill Management - skill 	Template Skills
63	Time management and prioritization.	Skill from template: Skill Management - skill 	Template Skills
64	6. Certifications (Common)	Skill from template: Skill Management - skill 	Template Skills
65	Law degree (LLB/JD)	Skill from template: Skill Management - skill 	Template Skills
66	LPC (Legal Practice Course) or equivalent	Skill from template: Skill Management - skill 	Template Skills
67	CILEX (Chartered Institute of Legal Executives)	Skill from template: Skill Management - skill 	Template Skills
68	Specialist certifications (e.g., GDPR Practitioner, Employment Law)	Skill from template: Skill Management - skill 	Template Skills
69	hdjhdc - Sample Skill 1765160831795	Sample skill for hdjhdc category	hdjhdc
70	Conflict Resolution	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
71	Job design	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
72	Interviewing	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
73	Onboarding	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
74	Reward Strategies	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
75	Benchmarking	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
76	Creating Contracts	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
77	Compliance & Record Keeping	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
78	Appraisals	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
79	Goal Setting	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
80	Feedback Systems	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
81	Workforce Planning	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
82	Succession Planning	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
83	Organisational Design & Development	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
84	Change Management	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
85	Diversity, Equity & Inclusion (DEI)	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
86	Employee Engagement	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
87	Employment law and regulations	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
88	GDPR and data privacy	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
89	Health & safety compliance	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
90	Policy development and auditing	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
91	Template Skill 1033	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
92	HRIS systems (Dynamics)	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
93	Data analytics for HR metrics (turnover, engagement)	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
94	Digital tools for recruitment and onboarding	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
95	Automation in HR processes	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
96	Communication and influencing	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
97	Coaching and mentoring	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
98	Problem-solving and decision-making	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
99	Emotional intelligence and empathy	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
100	Negotiation and conflict resolution	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
101	CIPD Levels 3, 5, 7	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
102	SHRM-CP / SHRM-SCP	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
103	Employment Law certifications	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
104	Coaching qualifications	Skill from template: Skill Management - Corp_Functions_Pathways_P&C	Template Skills
105	Brand Management	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
106	Campaign Planning & Execution	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
107	Content Creation	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
108	Digital Marketing	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
109	Market Research & Analysis	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
110	Internal Communications	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
111	External Communications	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
112	Crisis Communication	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
113	Presentation & Public Speaking	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
114	Social Media Management	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
115	Analytics Tools	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
116	Marketing Automation	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
117	Content Management Systems (CMS)	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
118	Template Skill 1019	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
119	Graphic Design Basics	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
120	Video Production	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
121	UX Writing	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
122	Strong written and verbal communication.	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
123	Creativity and innovation.	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
124	Stakeholder management and collaboration.	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
125	Project management and time management.	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
126	Adaptability and problem-solving.	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
127	CIM (Chartered Institute of Marketing)	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
128	Google Ads & Analytics Certifications	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
129	HubSpot Inbound Marketing	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
130	PRINCE2 (for campaign/project management)	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
131	CIPR (Chartered Institute of Public Relations)	Skill from template: Skill Management - Corp_Functions_Pathways_Mkt_Com	Template Skills
132	Networking	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
133	Operating Systems	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
134	Hardware & Infrastructure	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
135	Cloud Computing	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
136	Cybersecurity Basics	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
137	Programming	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
138	Database Management	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
139	Application Support	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
140	DevOps Practices	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
141	Incident & Problem Management	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
142	Change & Release Management	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
143	Monitoring & Performance	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
144	Collaboration Tools	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
145	Version Control	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
146	Virtualization & Cloud Tools	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
147	Troubleshooting and analytical thinking.	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
148	Communication and stakeholder engagement.	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
149	Adaptability and continuous learning.	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
150	CompTIA A+, Network+, Security+	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
151	Microsoft Certified	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
152	AWS Certified Solutions Architect	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
153	Cisco CCNA	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
154	ITIL Foundation	Skill from template: Skill Management - Corp_Functions_Pathways_IT	Template Skills
\.


--
-- TOC entry 3949 (class 0 OID 80033)
-- Dependencies: 218
-- Data for Name: team_skill_templates; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.team_skill_templates (id, team, skill_id, is_required, display_order) FROM stdin;
\.


--
-- TOC entry 3961 (class 0 OID 80189)
-- Dependencies: 230
-- Data for Name: template_assignments; Type: TABLE DATA; Schema: public; Owner: skillboard
--

COPY public.template_assignments (id, template_id, employee_id, assigned_by, assigned_at, status, category_hr) FROM stdin;
5	52	6	3	2025-12-07 13:01:29.486272	Completed	Technical Delivery
7	58	1	3	2025-12-07 13:58:15.668299	Completed	\N
6	57	1	3	2025-12-07 13:36:51.201168	Completed	\N
9	57	6	3	2025-12-08 04:48:56.727541	Completed	\N
10	58	6	3	2025-12-08 05:43:36.267954	Completed	\N
11	55	6	3	2025-12-08 05:48:38.850195	Completed	\N
12	54	6	3	2025-12-08 05:57:48.779112	Completed	\N
13	54	1	3	2025-12-08 07:20:31.119555	Pending	\N
\.


--
-- TOC entry 3943 (class 0 OID 79983)
-- Dependencies: 212
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, employee_id, email, password_hash, is_active, is_admin, must_change_password, created_at) FROM stdin;
1	E001	stalinj4747@gmail.com	$2b$12$GY9vNLuPcHNnIqjIZvuMnemM/eijFtNJLQ7Wro.BkBDgI9K3z.Ita	t	f	f	2025-12-06 13:42:24.84888
4	EMP001	alice@skillboard.com	$2b$12$L9vizX/185wOPGo8N.Qx7.5vofTRObEnM1aW0uuU6y.fzTX/SnpUq	t	f	f	2025-12-07 04:54:22.184266
5	EMP002	bob@skillboard.com	$2b$12$aWPfYpUUkV9JLgHhVsL8hOYd6NfnLMhJXmXzP2oUgcngBzZZJgm4C	t	f	f	2025-12-07 04:54:22.184272
6	EMP003	charlie@skillboard.com	$2b$12$U1PkW/qwxyphLqs48EsPCO.cDkbsabUUHWcRW3tcCuytlwOitfqUG	t	f	f	2025-12-07 04:54:22.184273
7	EMP004	david@skillboard.com	$2b$12$eob9t8rHpGmGD8X6fWgIk.kb9UQ.10kK.1AMrhLKs2woptX1//yN6	t	f	f	2025-12-07 04:54:22.184274
8	EMP005	eve@skillboard.com	$2b$12$AK6i/.VbsfWatTKswhasUuqDmEukj5NMPUl11ER299MQ5X1g1qXBG	t	f	f	2025-12-07 04:54:22.184274
3	\N	admin@skillboard.com	$2b$12$YfxcC5ta419I5LsZMbHqUONnL091Z/lX8/FXW.AWLXPZPfqsGsyoe	t	t	f	2025-12-06 13:46:40.05258
\.


--
-- TOC entry 4005 (class 0 OID 0)
-- Dependencies: 221
-- Name: category_skill_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.category_skill_templates_id_seq', 1, false);


--
-- TOC entry 4006 (class 0 OID 0)
-- Dependencies: 225
-- Name: course_assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.course_assignments_id_seq', 24, true);


--
-- TOC entry 4007 (class 0 OID 0)
-- Dependencies: 223
-- Name: courses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.courses_id_seq', 6, true);


--
-- TOC entry 4008 (class 0 OID 0)
-- Dependencies: 215
-- Name: employee_skills_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.employee_skills_id_seq', 23, true);


--
-- TOC entry 4009 (class 0 OID 0)
-- Dependencies: 231
-- Name: employee_template_responses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: skillboard
--

SELECT pg_catalog.setval('public.employee_template_responses_id_seq', 400, true);


--
-- TOC entry 4010 (class 0 OID 0)
-- Dependencies: 213
-- Name: employees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.employees_id_seq', 10, true);


--
-- TOC entry 4011 (class 0 OID 0)
-- Dependencies: 219
-- Name: role_requirements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.role_requirements_id_seq', 1, false);


--
-- TOC entry 4012 (class 0 OID 0)
-- Dependencies: 233
-- Name: skill_gap_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: skillboard
--

SELECT pg_catalog.setval('public.skill_gap_results_id_seq', 193, true);


--
-- TOC entry 4013 (class 0 OID 0)
-- Dependencies: 227
-- Name: skill_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.skill_templates_id_seq', 58, true);


--
-- TOC entry 4014 (class 0 OID 0)
-- Dependencies: 209
-- Name: skills_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.skills_id_seq', 154, true);


--
-- TOC entry 4015 (class 0 OID 0)
-- Dependencies: 217
-- Name: team_skill_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.team_skill_templates_id_seq', 1, false);


--
-- TOC entry 4016 (class 0 OID 0)
-- Dependencies: 229
-- Name: template_assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: skillboard
--

SELECT pg_catalog.setval('public.template_assignments_id_seq', 13, true);


--
-- TOC entry 4017 (class 0 OID 0)
-- Dependencies: 211
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 8, true);


--
-- TOC entry 3749 (class 2606 OID 80076)
-- Name: category_skill_templates category_skill_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_skill_templates
    ADD CONSTRAINT category_skill_templates_pkey PRIMARY KEY (id);


--
-- TOC entry 3759 (class 2606 OID 80114)
-- Name: course_assignments course_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_assignments
    ADD CONSTRAINT course_assignments_pkey PRIMARY KEY (id);


--
-- TOC entry 3755 (class 2606 OID 80094)
-- Name: courses courses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (id);


--
-- TOC entry 3730 (class 2606 OID 80018)
-- Name: employee_skills employee_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_pkey PRIMARY KEY (id);


--
-- TOC entry 3776 (class 2606 OID 80234)
-- Name: employee_template_responses employee_template_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.employee_template_responses
    ADD CONSTRAINT employee_template_responses_pkey PRIMARY KEY (id);


--
-- TOC entry 3721 (class 2606 OID 80002)
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (id);


--
-- TOC entry 3745 (class 2606 OID 80058)
-- Name: role_requirements role_requirements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_requirements
    ADD CONSTRAINT role_requirements_pkey PRIMARY KEY (id);


--
-- TOC entry 3780 (class 2606 OID 80256)
-- Name: skill_gap_results skill_gap_results_pkey; Type: CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.skill_gap_results
    ADD CONSTRAINT skill_gap_results_pkey PRIMARY KEY (id);


--
-- TOC entry 3769 (class 2606 OID 80148)
-- Name: skill_templates skill_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.skill_templates
    ADD CONSTRAINT skill_templates_pkey PRIMARY KEY (id);


--
-- TOC entry 3714 (class 2606 OID 79978)
-- Name: skills skills_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_pkey PRIMARY KEY (id);


--
-- TOC entry 3737 (class 2606 OID 80040)
-- Name: team_skill_templates team_skill_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_skill_templates
    ADD CONSTRAINT team_skill_templates_pkey PRIMARY KEY (id);


--
-- TOC entry 3772 (class 2606 OID 80196)
-- Name: template_assignments template_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.template_assignments
    ADD CONSTRAINT template_assignments_pkey PRIMARY KEY (id);


--
-- TOC entry 3782 (class 2606 OID 80258)
-- Name: skill_gap_results uq_assignment_skill_gap; Type: CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.skill_gap_results
    ADD CONSTRAINT uq_assignment_skill_gap UNIQUE (assignment_id, skill_id);


--
-- TOC entry 3747 (class 2606 OID 80060)
-- Name: role_requirements uq_band_skill_requirement; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_requirements
    ADD CONSTRAINT uq_band_skill_requirement UNIQUE (band, skill_id);


--
-- TOC entry 3753 (class 2606 OID 80078)
-- Name: category_skill_templates uq_category_skill_template; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_skill_templates
    ADD CONSTRAINT uq_category_skill_template UNIQUE (category, skill_id);


--
-- TOC entry 3765 (class 2606 OID 80116)
-- Name: course_assignments uq_employee_course_assignment; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_assignments
    ADD CONSTRAINT uq_employee_course_assignment UNIQUE (employee_id, course_id);


--
-- TOC entry 3733 (class 2606 OID 80020)
-- Name: employee_skills uq_employee_skill; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT uq_employee_skill UNIQUE (employee_id, skill_id);


--
-- TOC entry 3739 (class 2606 OID 80042)
-- Name: team_skill_templates uq_team_skill_template; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_skill_templates
    ADD CONSTRAINT uq_team_skill_template UNIQUE (team, skill_id);


--
-- TOC entry 3774 (class 2606 OID 80198)
-- Name: template_assignments uq_template_employee_assignment; Type: CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.template_assignments
    ADD CONSTRAINT uq_template_employee_assignment UNIQUE (template_id, employee_id);


--
-- TOC entry 3719 (class 2606 OID 79990)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 3760 (class 1259 OID 80136)
-- Name: idx_course_assignments_course_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_course_assignments_course_id ON public.course_assignments USING btree (course_id);


--
-- TOC entry 3761 (class 1259 OID 80137)
-- Name: idx_course_assignments_employee_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_course_assignments_employee_id ON public.course_assignments USING btree (employee_id);


--
-- TOC entry 3762 (class 1259 OID 80138)
-- Name: idx_course_assignments_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_course_assignments_status ON public.course_assignments USING btree (status);


--
-- TOC entry 3756 (class 1259 OID 80135)
-- Name: idx_courses_skill_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_courses_skill_id ON public.courses USING btree (skill_id);


--
-- TOC entry 3740 (class 1259 OID 80133)
-- Name: idx_role_requirements_band; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_role_requirements_band ON public.role_requirements USING btree (band);


--
-- TOC entry 3741 (class 1259 OID 80134)
-- Name: idx_role_requirements_skill_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_role_requirements_skill_id ON public.role_requirements USING btree (skill_id);


--
-- TOC entry 3750 (class 1259 OID 80085)
-- Name: ix_category_skill_templates_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_category_skill_templates_category ON public.category_skill_templates USING btree (category);


--
-- TOC entry 3751 (class 1259 OID 80084)
-- Name: ix_category_skill_templates_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_category_skill_templates_id ON public.category_skill_templates USING btree (id);


--
-- TOC entry 3763 (class 1259 OID 80132)
-- Name: ix_course_assignments_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_course_assignments_id ON public.course_assignments USING btree (id);


--
-- TOC entry 3757 (class 1259 OID 80105)
-- Name: ix_courses_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_courses_id ON public.courses USING btree (id);


--
-- TOC entry 3731 (class 1259 OID 80031)
-- Name: ix_employee_skills_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_employee_skills_id ON public.employee_skills USING btree (id);


--
-- TOC entry 3777 (class 1259 OID 80247)
-- Name: ix_employee_template_responses_id; Type: INDEX; Schema: public; Owner: skillboard
--

CREATE INDEX ix_employee_template_responses_id ON public.employee_template_responses USING btree (id);


--
-- TOC entry 3722 (class 1259 OID 80009)
-- Name: ix_employees_band; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_employees_band ON public.employees USING btree (band);


--
-- TOC entry 3723 (class 1259 OID 80003)
-- Name: ix_employees_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_employees_category ON public.employees USING btree (category);


--
-- TOC entry 3724 (class 1259 OID 80004)
-- Name: ix_employees_company_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_employees_company_email ON public.employees USING btree (company_email);


--
-- TOC entry 3725 (class 1259 OID 80005)
-- Name: ix_employees_employee_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_employees_employee_id ON public.employees USING btree (employee_id);


--
-- TOC entry 3726 (class 1259 OID 80008)
-- Name: ix_employees_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_employees_id ON public.employees USING btree (id);


--
-- TOC entry 3727 (class 1259 OID 80006)
-- Name: ix_employees_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_employees_name ON public.employees USING btree (name);


--
-- TOC entry 3728 (class 1259 OID 80007)
-- Name: ix_employees_team; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_employees_team ON public.employees USING btree (team);


--
-- TOC entry 3742 (class 1259 OID 80067)
-- Name: ix_role_requirements_band; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_role_requirements_band ON public.role_requirements USING btree (band);


--
-- TOC entry 3743 (class 1259 OID 80066)
-- Name: ix_role_requirements_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_role_requirements_id ON public.role_requirements USING btree (id);


--
-- TOC entry 3778 (class 1259 OID 80269)
-- Name: ix_skill_gap_results_id; Type: INDEX; Schema: public; Owner: skillboard
--

CREATE INDEX ix_skill_gap_results_id ON public.skill_gap_results USING btree (id);


--
-- TOC entry 3766 (class 1259 OID 80155)
-- Name: ix_skill_templates_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_skill_templates_id ON public.skill_templates USING btree (id);


--
-- TOC entry 3767 (class 1259 OID 80154)
-- Name: ix_skill_templates_template_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_skill_templates_template_name ON public.skill_templates USING btree (template_name);


--
-- TOC entry 3710 (class 1259 OID 79979)
-- Name: ix_skills_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_skills_category ON public.skills USING btree (category);


--
-- TOC entry 3711 (class 1259 OID 79980)
-- Name: ix_skills_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_skills_id ON public.skills USING btree (id);


--
-- TOC entry 3712 (class 1259 OID 79981)
-- Name: ix_skills_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_skills_name ON public.skills USING btree (name);


--
-- TOC entry 3734 (class 1259 OID 80048)
-- Name: ix_team_skill_templates_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_team_skill_templates_id ON public.team_skill_templates USING btree (id);


--
-- TOC entry 3735 (class 1259 OID 80049)
-- Name: ix_team_skill_templates_team; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_team_skill_templates_team ON public.team_skill_templates USING btree (team);


--
-- TOC entry 3770 (class 1259 OID 80214)
-- Name: ix_template_assignments_id; Type: INDEX; Schema: public; Owner: skillboard
--

CREATE INDEX ix_template_assignments_id ON public.template_assignments USING btree (id);


--
-- TOC entry 3715 (class 1259 OID 79993)
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- TOC entry 3716 (class 1259 OID 79992)
-- Name: ix_users_employee_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_employee_id ON public.users USING btree (employee_id);


--
-- TOC entry 3717 (class 1259 OID 79991)
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- TOC entry 3787 (class 2606 OID 80079)
-- Name: category_skill_templates category_skill_templates_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_skill_templates
    ADD CONSTRAINT category_skill_templates_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id);


--
-- TOC entry 3790 (class 2606 OID 80127)
-- Name: course_assignments course_assignments_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_assignments
    ADD CONSTRAINT course_assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- TOC entry 3791 (class 2606 OID 80117)
-- Name: course_assignments course_assignments_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_assignments
    ADD CONSTRAINT course_assignments_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id);


--
-- TOC entry 3792 (class 2606 OID 80122)
-- Name: course_assignments course_assignments_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_assignments
    ADD CONSTRAINT course_assignments_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- TOC entry 3788 (class 2606 OID 80100)
-- Name: courses courses_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3789 (class 2606 OID 80095)
-- Name: courses courses_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id);


--
-- TOC entry 3783 (class 2606 OID 80021)
-- Name: employee_skills employee_skills_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- TOC entry 3784 (class 2606 OID 80026)
-- Name: employee_skills employee_skills_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id);


--
-- TOC entry 3797 (class 2606 OID 80237)
-- Name: employee_template_responses employee_template_responses_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.employee_template_responses
    ADD CONSTRAINT employee_template_responses_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES public.template_assignments(id);


--
-- TOC entry 3798 (class 2606 OID 80242)
-- Name: employee_template_responses employee_template_responses_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.employee_template_responses
    ADD CONSTRAINT employee_template_responses_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id);


--
-- TOC entry 3786 (class 2606 OID 80061)
-- Name: role_requirements role_requirements_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_requirements
    ADD CONSTRAINT role_requirements_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id);


--
-- TOC entry 3799 (class 2606 OID 80259)
-- Name: skill_gap_results skill_gap_results_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.skill_gap_results
    ADD CONSTRAINT skill_gap_results_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES public.template_assignments(id);


--
-- TOC entry 3800 (class 2606 OID 80264)
-- Name: skill_gap_results skill_gap_results_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.skill_gap_results
    ADD CONSTRAINT skill_gap_results_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id);


--
-- TOC entry 3793 (class 2606 OID 80149)
-- Name: skill_templates skill_templates_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.skill_templates
    ADD CONSTRAINT skill_templates_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id);


--
-- TOC entry 3785 (class 2606 OID 80043)
-- Name: team_skill_templates team_skill_templates_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_skill_templates
    ADD CONSTRAINT team_skill_templates_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id);


--
-- TOC entry 3794 (class 2606 OID 80209)
-- Name: template_assignments template_assignments_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.template_assignments
    ADD CONSTRAINT template_assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- TOC entry 3795 (class 2606 OID 80204)
-- Name: template_assignments template_assignments_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.template_assignments
    ADD CONSTRAINT template_assignments_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- TOC entry 3796 (class 2606 OID 80199)
-- Name: template_assignments template_assignments_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillboard
--

ALTER TABLE ONLY public.template_assignments
    ADD CONSTRAINT template_assignments_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.skill_templates(id);


--
-- TOC entry 3971 (class 0 OID 0)
-- Dependencies: 4
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: stalin_j
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- TOC entry 3972 (class 0 OID 0)
-- Dependencies: 222
-- Name: TABLE category_skill_templates; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE public.category_skill_templates TO skillboard;


--
-- TOC entry 3974 (class 0 OID 0)
-- Dependencies: 221
-- Name: SEQUENCE category_skill_templates_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.category_skill_templates_id_seq TO skillboard;


--
-- TOC entry 3975 (class 0 OID 0)
-- Dependencies: 226
-- Name: TABLE course_assignments; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE public.course_assignments TO skillboard;


--
-- TOC entry 3977 (class 0 OID 0)
-- Dependencies: 225
-- Name: SEQUENCE course_assignments_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.course_assignments_id_seq TO skillboard;


--
-- TOC entry 3978 (class 0 OID 0)
-- Dependencies: 224
-- Name: TABLE courses; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE public.courses TO skillboard;


--
-- TOC entry 3980 (class 0 OID 0)
-- Dependencies: 223
-- Name: SEQUENCE courses_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.courses_id_seq TO skillboard;


--
-- TOC entry 3981 (class 0 OID 0)
-- Dependencies: 216
-- Name: TABLE employee_skills; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE public.employee_skills TO skillboard;


--
-- TOC entry 3983 (class 0 OID 0)
-- Dependencies: 215
-- Name: SEQUENCE employee_skills_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.employee_skills_id_seq TO skillboard;


--
-- TOC entry 3985 (class 0 OID 0)
-- Dependencies: 214
-- Name: TABLE employees; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE public.employees TO skillboard;


--
-- TOC entry 3987 (class 0 OID 0)
-- Dependencies: 213
-- Name: SEQUENCE employees_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.employees_id_seq TO skillboard;


--
-- TOC entry 3988 (class 0 OID 0)
-- Dependencies: 220
-- Name: TABLE role_requirements; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE public.role_requirements TO skillboard;


--
-- TOC entry 3990 (class 0 OID 0)
-- Dependencies: 219
-- Name: SEQUENCE role_requirements_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.role_requirements_id_seq TO skillboard;


--
-- TOC entry 3992 (class 0 OID 0)
-- Dependencies: 228
-- Name: TABLE skill_templates; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE public.skill_templates TO skillboard;


--
-- TOC entry 3994 (class 0 OID 0)
-- Dependencies: 227
-- Name: SEQUENCE skill_templates_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.skill_templates_id_seq TO skillboard;


--
-- TOC entry 3995 (class 0 OID 0)
-- Dependencies: 210
-- Name: TABLE skills; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE public.skills TO skillboard;


--
-- TOC entry 3997 (class 0 OID 0)
-- Dependencies: 209
-- Name: SEQUENCE skills_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.skills_id_seq TO skillboard;


--
-- TOC entry 3998 (class 0 OID 0)
-- Dependencies: 218
-- Name: TABLE team_skill_templates; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE public.team_skill_templates TO skillboard;


--
-- TOC entry 4000 (class 0 OID 0)
-- Dependencies: 217
-- Name: SEQUENCE team_skill_templates_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.team_skill_templates_id_seq TO skillboard;


--
-- TOC entry 4002 (class 0 OID 0)
-- Dependencies: 212
-- Name: TABLE users; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE public.users TO skillboard;


--
-- TOC entry 4004 (class 0 OID 0)
-- Dependencies: 211
-- Name: SEQUENCE users_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.users_id_seq TO skillboard;


-- Completed on 2025-12-08 14:05:25 IST

--
-- PostgreSQL database dump complete
--


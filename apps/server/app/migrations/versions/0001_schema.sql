CREATE TABLE user (
	name TEXT NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CHECK (name = 'local'), 
	UNIQUE (name), 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE collection (
	name TEXT NOT NULL, 
	cover_artwork_id VARCHAR(26), 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(cover_artwork_id) REFERENCES artwork (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("cover_artwork_id")=26 AND substr("cover_artwork_id",1,1) BETWEEN '0' AND '7' AND "cover_artwork_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE song (
	collection_id VARCHAR(26), 
	title TEXT NOT NULL, 
	artist TEXT, 
	status TEXT DEFAULT 'draft' NOT NULL, 
	style_prompt TEXT DEFAULT '' NOT NULL, 
	negative_prompt TEXT, 
	language TEXT, 
	current_lyrics_version_id VARCHAR(26), 
	master_take_id VARCHAR(26), 
	cover_artwork_id VARCHAR(26), 
	tags JSON DEFAULT '[]' NOT NULL, 
	notes TEXT, 
	rev INTEGER DEFAULT '1' NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_status CHECK (status IN ('draft','in_progress','final','archived')), 
	CHECK (rev >= 1), 
	FOREIGN KEY(collection_id) REFERENCES collection (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(current_lyrics_version_id) REFERENCES lyrics_version (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(master_take_id) REFERENCES take (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(cover_artwork_id) REFERENCES artwork (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("collection_id")=26 AND substr("collection_id",1,1) BETWEEN '0' AND '7' AND "collection_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("current_lyrics_version_id")=26 AND substr("current_lyrics_version_id",1,1) BETWEEN '0' AND '7' AND "current_lyrics_version_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("master_take_id")=26 AND substr("master_take_id",1,1) BETWEEN '0' AND '7' AND "master_take_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("cover_artwork_id")=26 AND substr("cover_artwork_id",1,1) BETWEEN '0' AND '7' AND "cover_artwork_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("tags" IS NULL OR (json_valid("tags") AND json_type("tags")='array')), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE lyrics_version (
	song_id VARCHAR(26) NOT NULL, 
	text TEXT NOT NULL, 
	source TEXT NOT NULL, 
	declaration TEXT NOT NULL, 
	parent_id VARCHAR(26), 
	sha256 VARCHAR(64) NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_source CHECK (source IN ('manual','assistant','import')), 
	CONSTRAINT ck_declaration CHECK (declaration IN ('own','assistant','public_domain','licensed')), 
	FOREIGN KEY(song_id) REFERENCES song (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(parent_id) REFERENCES lyrics_version (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("song_id")=26 AND substr("song_id",1,1) BETWEEN '0' AND '7' AND "song_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("parent_id")=26 AND substr("parent_id",1,1) BETWEEN '0' AND '7' AND "parent_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("sha256")=64 AND "sha256" NOT GLOB '*[^0-9a-f]*'), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE take (
	song_id VARCHAR(26) NOT NULL, 
	job_id VARCHAR(26) NOT NULL, 
	lyrics_version_id VARCHAR(26), 
	status TEXT DEFAULT 'queued' NOT NULL, 
	batch_id VARCHAR(26) NOT NULL, 
	variant_index INTEGER DEFAULT '0' NOT NULL, 
	root_id VARCHAR(26) NOT NULL, 
	derivation TEXT NOT NULL, 
	task TEXT NOT NULL, 
	model_id TEXT NOT NULL, 
	model_version TEXT NOT NULL, 
	seed TEXT NOT NULL, 
	params JSON DEFAULT '{}' NOT NULL, 
	duration_s FLOAT, 
	sample_rate INTEGER, 
	rating INTEGER, 
	favorite BOOLEAN DEFAULT '0' NOT NULL, 
	label TEXT, 
	commercial_use BOOLEAN NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_status CHECK (status IN ('queued','running','ready','failed','cancelled')), 
	CONSTRAINT ck_derivation CHECK (derivation IN ('original','variant','extend','repaint','cover','complete','remaster','edit')), 
	CHECK (variant_index >= 0), 
	CHECK (rating IS NULL OR rating BETWEEN 1 AND 5), 
	CHECK (duration_s IS NULL OR duration_s >= 0), 
	CHECK (sample_rate IS NULL OR sample_rate > 0), 
	FOREIGN KEY(song_id) REFERENCES song (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(job_id) REFERENCES job (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(lyrics_version_id) REFERENCES lyrics_version (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(root_id) REFERENCES take (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("song_id")=26 AND substr("song_id",1,1) BETWEEN '0' AND '7' AND "song_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("job_id")=26 AND substr("job_id",1,1) BETWEEN '0' AND '7' AND "job_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("lyrics_version_id")=26 AND substr("lyrics_version_id",1,1) BETWEEN '0' AND '7' AND "lyrics_version_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("batch_id")=26 AND substr("batch_id",1,1) BETWEEN '0' AND '7' AND "batch_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("root_id")=26 AND substr("root_id",1,1) BETWEEN '0' AND '7' AND "root_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("seed")>0 AND "seed" NOT GLOB '*[^0-9]*' AND ("seed"='0' OR substr("seed",1,1)!='0')), 
	CHECK ("params" IS NULL OR (json_valid("params") AND json_type("params")='object')), 
	CHECK (abs("duration_s") <= 1.7976931348623157e308), 
	CHECK ("favorite" IN (0,1)), 
	CHECK ("commercial_use" IN (0,1)), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE lineage_edge (
	child_type TEXT NOT NULL, 
	child_id VARCHAR(26) NOT NULL, 
	parent_type TEXT NOT NULL, 
	parent_id VARCHAR(26) NOT NULL, 
	role TEXT NOT NULL, 
	section_map JSON, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (child_type, child_id, parent_type, parent_id, role), 
	CHECK (child_type != parent_type OR child_id != parent_id), 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("child_id")=26 AND substr("child_id",1,1) BETWEEN '0' AND '7' AND "child_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("parent_id")=26 AND substr("parent_id",1,1) BETWEEN '0' AND '7' AND "parent_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("section_map" IS NULL OR (json_valid("section_map") AND json_type("section_map")='object')), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE asset (
	subject_type TEXT NOT NULL, 
	subject_id VARCHAR(26) NOT NULL, 
	role TEXT NOT NULL, 
	path TEXT NOT NULL, 
	media_type TEXT NOT NULL, 
	sha256 VARCHAR(64) NOT NULL, 
	bytes INTEGER NOT NULL, 
	meta JSON DEFAULT '{}' NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_subject_type CHECK (subject_type IN ('take','artwork','shot_version','render','export','character','lora','cli_run')), 
	CHECK (bytes >= 0), 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("subject_id")=26 AND substr("subject_id",1,1) BETWEEN '0' AND '7' AND "subject_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("path")>0 AND substr("path",1,1)!='/' AND instr("path",':')=0 AND instr("path",char(92))=0 AND instr('/'||"path"||'/','/../')=0), 
	CHECK (length("sha256")=64 AND "sha256" NOT GLOB '*[^0-9a-f]*'), 
	CHECK ("meta" IS NULL OR (json_valid("meta") AND json_type("meta")='object')), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE upload (
	kind TEXT NOT NULL, 
	path TEXT NOT NULL, 
	sha256 VARCHAR(64) NOT NULL, 
	media_type TEXT NOT NULL, 
	meta JSON DEFAULT '{}' NOT NULL, 
	rights TEXT NOT NULL, 
	real_person BOOLEAN DEFAULT '0' NOT NULL, 
	consent TEXT NOT NULL, 
	note TEXT, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_kind CHECK (kind IN ('audio','image')), 
	CONSTRAINT ck_rights CHECK (rights IN ('own','licensed','consented','public_domain')), 
	CONSTRAINT ck_consent CHECK (consent IN ('self','consented','n_a')), 
	CHECK (NOT real_person OR consent IN ('self','consented')), 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("path")>0 AND substr("path",1,1)!='/' AND instr("path",':')=0 AND instr("path",char(92))=0 AND instr('/'||"path"||'/','/../')=0), 
	CHECK (length("sha256")=64 AND "sha256" NOT GLOB '*[^0-9a-f]*'), 
	CHECK ("meta" IS NULL OR (json_valid("meta") AND json_type("meta")='object')), 
	CHECK ("real_person" IN (0,1)), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE analysis (
	take_id VARCHAR(26) NOT NULL, 
	kind TEXT NOT NULL, 
	analyzer_id TEXT NOT NULL, 
	analyzer_version TEXT NOT NULL, 
	lyrics_version_id VARCHAR(26), 
	data JSON NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (take_id, kind, analyzer_id), 
	CONSTRAINT ck_kind CHECK (kind IN ('beats','sections','key','loudness','lyrics_timing')), 
	FOREIGN KEY(take_id) REFERENCES take (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(lyrics_version_id) REFERENCES lyrics_version (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("take_id")=26 AND substr("take_id",1,1) BETWEEN '0' AND '7' AND "take_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("lyrics_version_id")=26 AND substr("lyrics_version_id",1,1) BETWEEN '0' AND '7' AND "lyrics_version_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("data" IS NULL OR (json_valid("data") AND json_type("data")='object')), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE artwork (
	song_id VARCHAR(26), 
	kind TEXT NOT NULL, 
	source TEXT NOT NULL, 
	upload_id VARCHAR(26), 
	job_id VARCHAR(26), 
	prompt TEXT, 
	model_id TEXT, 
	seed TEXT, 
	rights TEXT NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_kind CHECK (kind IN ('cover','keyframe','background')), 
	CONSTRAINT ck_source CHECK (source IN ('generated','upload')), 
	CONSTRAINT ck_rights CHECK (rights IN ('own','licensed','consented','public_domain')), 
	FOREIGN KEY(song_id) REFERENCES song (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(upload_id) REFERENCES upload (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(job_id) REFERENCES job (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("song_id")=26 AND substr("song_id",1,1) BETWEEN '0' AND '7' AND "song_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("upload_id")=26 AND substr("upload_id",1,1) BETWEEN '0' AND '7' AND "upload_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("job_id")=26 AND substr("job_id",1,1) BETWEEN '0' AND '7' AND "job_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("seed")>0 AND "seed" NOT GLOB '*[^0-9]*' AND ("seed"='0' OR substr("seed",1,1)!='0')), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE character (
	name TEXT NOT NULL, 
	description TEXT NOT NULL, 
	kind TEXT NOT NULL, 
	consent TEXT NOT NULL, 
	consent_note TEXT, 
	sheet_artwork_id VARCHAR(26), 
	lora_asset_id VARCHAR(26), 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_kind CHECK (kind IN ('real_person','fictional','animal','object')), 
	CONSTRAINT ck_consent CHECK (consent IN ('self','consented','fictional')), 
	CHECK (kind != 'real_person' OR consent IN ('self','consented')), 
	FOREIGN KEY(sheet_artwork_id) REFERENCES artwork (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(lora_asset_id) REFERENCES asset (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("sheet_artwork_id")=26 AND substr("sheet_artwork_id",1,1) BETWEEN '0' AND '7' AND "sheet_artwork_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("lora_asset_id")=26 AND substr("lora_asset_id",1,1) BETWEEN '0' AND '7' AND "lora_asset_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE character_ref (
	character_id VARCHAR(26) NOT NULL, 
	upload_id VARCHAR(26), 
	artwork_id VARCHAR(26), 
	"view" TEXT, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CHECK ((upload_id IS NULL) != (artwork_id IS NULL)), 
	CHECK (view IS NULL OR view IN ('front','profile','full','expression')), 
	FOREIGN KEY(character_id) REFERENCES character (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(upload_id) REFERENCES upload (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(artwork_id) REFERENCES artwork (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("character_id")=26 AND substr("character_id",1,1) BETWEEN '0' AND '7' AND "character_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("upload_id")=26 AND substr("upload_id",1,1) BETWEEN '0' AND '7' AND "upload_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("artwork_id")=26 AND substr("artwork_id",1,1) BETWEEN '0' AND '7' AND "artwork_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE preset (
	kind TEXT NOT NULL, 
	name TEXT NOT NULL, 
	payload JSON NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_kind CHECK (kind IN ('style','voice','visual','full')), 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK ("payload" IS NULL OR (json_valid("payload") AND json_type("payload")='object')), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE video_project (
	song_id VARCHAR(26) NOT NULL, 
	take_id VARCHAR(26) NOT NULL, 
	title TEXT NOT NULL, 
	aspect TEXT NOT NULL, 
	level_preset TEXT NOT NULL, 
	visual_style TEXT NOT NULL, 
	treatment TEXT NOT NULL, 
	status TEXT DEFAULT 'planning' NOT NULL, 
	timeline JSON NOT NULL, 
	rev INTEGER DEFAULT '1' NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_aspect CHECK (aspect IN ('16:9','9:16','1:1')), 
	CONSTRAINT ck_level_preset CHECK (level_preset IN ('N0','N1','N2','N3')), 
	CONSTRAINT ck_status CHECK (status IN ('planning','generating','editing','rendered')), 
	CHECK (rev >= 1), 
	FOREIGN KEY(song_id) REFERENCES song (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(take_id) REFERENCES take (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("song_id")=26 AND substr("song_id",1,1) BETWEEN '0' AND '7' AND "song_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("take_id")=26 AND substr("take_id",1,1) BETWEEN '0' AND '7' AND "take_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("timeline" IS NULL OR (json_valid("timeline") AND json_type("timeline")='object')), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE video_character (
	video_project_id VARCHAR(26) NOT NULL, 
	character_id VARCHAR(26) NOT NULL, 
	role TEXT NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (video_project_id, character_id, role), 
	CONSTRAINT ck_role CHECK (role IN ('performer','cast')), 
	FOREIGN KEY(video_project_id) REFERENCES video_project (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(character_id) REFERENCES character (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("video_project_id")=26 AND substr("video_project_id",1,1) BETWEEN '0' AND '7' AND "video_project_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("character_id")=26 AND substr("character_id",1,1) BETWEEN '0' AND '7' AND "character_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE shot (
	video_project_id VARCHAR(26) NOT NULL, 
	"key" TEXT NOT NULL, 
	kind TEXT NOT NULL, 
	current_version_id VARCHAR(26), 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (video_project_id, "key"), 
	CONSTRAINT ck_kind CHECK (kind IN ('lyric','still','still_motion','i2v','singer','t2v')), 
	FOREIGN KEY(video_project_id) REFERENCES video_project (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(current_version_id) REFERENCES shot_version (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("video_project_id")=26 AND substr("video_project_id",1,1) BETWEEN '0' AND '7' AND "video_project_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("current_version_id")=26 AND substr("current_version_id",1,1) BETWEEN '0' AND '7' AND "current_version_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE shot_version (
	shot_id VARCHAR(26) NOT NULL, 
	job_id VARCHAR(26), 
	prompt TEXT NOT NULL, 
	camera TEXT, 
	seed TEXT, 
	model_id TEXT, 
	provider TEXT DEFAULT 'local' NOT NULL, 
	status TEXT DEFAULT 'queued' NOT NULL, 
	keyframe_asset_id VARCHAR(26), 
	clip_asset_id VARCHAR(26), 
	focus_point JSON, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_status CHECK (status IN ('queued','running','ready','failed','cancelled')), 
	FOREIGN KEY(shot_id) REFERENCES shot (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(job_id) REFERENCES job (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(keyframe_asset_id) REFERENCES asset (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(clip_asset_id) REFERENCES asset (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("shot_id")=26 AND substr("shot_id",1,1) BETWEEN '0' AND '7' AND "shot_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("job_id")=26 AND substr("job_id",1,1) BETWEEN '0' AND '7' AND "job_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("seed")>0 AND "seed" NOT GLOB '*[^0-9]*' AND ("seed"='0' OR substr("seed",1,1)!='0')), 
	CHECK (length("keyframe_asset_id")=26 AND substr("keyframe_asset_id",1,1) BETWEEN '0' AND '7' AND "keyframe_asset_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("clip_asset_id")=26 AND substr("clip_asset_id",1,1) BETWEEN '0' AND '7' AND "clip_asset_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("focus_point" IS NULL OR (json_valid("focus_point") AND json_type("focus_point")='array')), 
	CHECK (focus_point IS NULL OR (json_array_length(focus_point)=2 AND json_type(focus_point,'$[0]') IN ('integer','real') AND json_type(focus_point,'$[1]') IN ('integer','real') AND json_extract(focus_point,'$[0]') BETWEEN 0 AND 1 AND json_extract(focus_point,'$[1]') BETWEEN 0 AND 1)), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE render (
	video_project_id VARCHAR(26) NOT NULL, 
	timeline_rev INTEGER NOT NULL, 
	aspect TEXT NOT NULL, 
	resolution TEXT NOT NULL, 
	kind TEXT NOT NULL, 
	subtitles TEXT NOT NULL, 
	status TEXT DEFAULT 'queued' NOT NULL, 
	asset_id VARCHAR(26), 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_aspect CHECK (aspect IN ('16:9','9:16','1:1')), 
	CONSTRAINT ck_kind CHECK (kind IN ('full','short','preview')), 
	CONSTRAINT ck_subtitles CHECK (subtitles IN ('burned','srt','none')), 
	CONSTRAINT ck_status CHECK (status IN ('queued','running','ready','failed','cancelled')), 
	CHECK (timeline_rev >= 1), 
	FOREIGN KEY(video_project_id) REFERENCES video_project (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(asset_id) REFERENCES asset (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("video_project_id")=26 AND substr("video_project_id",1,1) BETWEEN '0' AND '7' AND "video_project_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (resolution NOT GLOB '*[^0-9x]*' AND instr(resolution,'x')>1 AND instr(substr(resolution,instr(resolution,'x')+1),'x')=0 AND CAST(substr(resolution,1,instr(resolution,'x')-1) AS INTEGER)>0 AND CAST(substr(resolution,instr(resolution,'x')+1) AS INTEGER)>0), 
	CHECK (length("asset_id")=26 AND substr("asset_id",1,1) BETWEEN '0' AND '7' AND "asset_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE export (
	song_id VARCHAR(26) NOT NULL, 
	kind TEXT NOT NULL, 
	target TEXT, 
	asset_id VARCHAR(26), 
	expires_at TEXT NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_kind CHECK (kind IN ('audio','stems','video','lyrics','project_zip')), 
	CHECK (target IS NULL OR target IN ('streaming','broadcast','podcast')), 
	FOREIGN KEY(song_id) REFERENCES song (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(asset_id) REFERENCES asset (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("song_id")=26 AND substr("song_id",1,1) BETWEEN '0' AND '7' AND "song_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("asset_id")=26 AND substr("asset_id",1,1) BETWEEN '0' AND '7' AND "asset_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("expires_at" IS NULL OR (substr("expires_at",-1)='Z' AND datetime("expires_at") IS NOT NULL)), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE job (
	task TEXT NOT NULL, 
	lane TEXT NOT NULL, 
	priority TEXT DEFAULT 'normal' NOT NULL, 
	not_before TEXT, 
	status TEXT DEFAULT 'queued' NOT NULL, 
	attempt INTEGER DEFAULT '0' NOT NULL, 
	max_attempts INTEGER DEFAULT '3' NOT NULL, 
	engine_id TEXT, 
	model_id TEXT, 
	request JSON NOT NULL, 
	stage TEXT, 
	progress FLOAT, 
	error_code TEXT, 
	error TEXT, 
	telemetry JSON, 
	song_id VARCHAR(26), 
	started_at TEXT, 
	finished_at TEXT, 
	cancel_requested_at TEXT, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_lane CHECK (lane IN ('gpu','cpu','remote')), 
	CONSTRAINT ck_priority CHECK (priority IN ('interactive','normal','batch','nightly')), 
	CONSTRAINT ck_status CHECK (status IN ('queued','blocked','running','succeeded','failed','cancelled','interrupted')), 
	CHECK (attempt >= 0 AND max_attempts >= 1 AND attempt <= max_attempts), 
	CHECK (progress IS NULL OR progress BETWEEN 0 AND 1), 
	FOREIGN KEY(song_id) REFERENCES song (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK ("not_before" IS NULL OR (substr("not_before",-1)='Z' AND datetime("not_before") IS NOT NULL)), 
	CHECK ("request" IS NULL OR (json_valid("request") AND json_type("request")='object')), 
	CHECK (abs("progress") <= 1.7976931348623157e308), 
	CHECK ("telemetry" IS NULL OR (json_valid("telemetry") AND json_type("telemetry")='object')), 
	CHECK (length("song_id")=26 AND substr("song_id",1,1) BETWEEN '0' AND '7' AND "song_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("started_at" IS NULL OR (substr("started_at",-1)='Z' AND datetime("started_at") IS NOT NULL)), 
	CHECK ("finished_at" IS NULL OR (substr("finished_at",-1)='Z' AND datetime("finished_at") IS NOT NULL)), 
	CHECK ("cancel_requested_at" IS NULL OR (substr("cancel_requested_at",-1)='Z' AND datetime("cancel_requested_at") IS NOT NULL)), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE job_dependency (
	job_id VARCHAR(26) NOT NULL, 
	depends_on_job_id VARCHAR(26) NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (job_id, depends_on_job_id), 
	CHECK (job_id != depends_on_job_id), 
	FOREIGN KEY(job_id) REFERENCES job (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(depends_on_job_id) REFERENCES job (id) DEFERRABLE INITIALLY DEFERRED, 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK (length("job_id")=26 AND substr("job_id",1,1) BETWEEN '0' AND '7' AND "job_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("depends_on_job_id")=26 AND substr("depends_on_job_id",1,1) BETWEEN '0' AND '7' AND "depends_on_job_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE setting (
	"key" TEXT NOT NULL, 
	value JSON NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (owner_id, "key"), 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK ("value" IS NULL OR (json_valid("value") AND json_type("value")='object')), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE TABLE provider (
	function TEXT NOT NULL, 
	name TEXT NOT NULL, 
	enabled BOOLEAN DEFAULT '0' NOT NULL, 
	config JSON DEFAULT '{}' NOT NULL, 
	id VARCHAR(26) NOT NULL, 
	owner_id VARCHAR(26) NOT NULL, 
	created_at TEXT NOT NULL, 
	updated_at TEXT NOT NULL, 
	deleted_at TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (owner_id, function, name), 
	FOREIGN KEY(owner_id) REFERENCES user (id) DEFERRABLE INITIALLY DEFERRED, 
	CHECK ("enabled" IN (0,1)), 
	CHECK ("config" IS NULL OR (json_valid("config") AND json_type("config")='object')), 
	CHECK (length("id")=26 AND substr("id",1,1) BETWEEN '0' AND '7' AND "id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK (length("owner_id")=26 AND substr("owner_id",1,1) BETWEEN '0' AND '7' AND "owner_id" NOT GLOB '*[^0123456789ABCDEFGHJKMNPQRSTVWXYZ]*'), 
	CHECK ("created_at" IS NULL OR (substr("created_at",-1)='Z' AND datetime("created_at") IS NOT NULL)), 
	CHECK ("updated_at" IS NULL OR (substr("updated_at",-1)='Z' AND datetime("updated_at") IS NOT NULL)), 
	CHECK ("deleted_at" IS NULL OR (substr("deleted_at",-1)='Z' AND datetime("deleted_at") IS NOT NULL))
);
CREATE INDEX ix_user_deleted_at ON user (deleted_at);
CREATE INDEX ix_user_owner_id ON user (owner_id);
CREATE INDEX ix_collection_cover_artwork_id ON collection (cover_artwork_id);
CREATE INDEX ix_collection_deleted_at ON collection (deleted_at);
CREATE INDEX ix_collection_owner_id ON collection (owner_id);
CREATE INDEX ix_song_collection_id ON song (collection_id);
CREATE INDEX ix_song_cover_artwork_id ON song (cover_artwork_id);
CREATE INDEX ix_song_current_lyrics_version_id ON song (current_lyrics_version_id);
CREATE INDEX ix_song_deleted_at ON song (deleted_at);
CREATE INDEX ix_song_library ON song (owner_id, deleted_at, updated_at);
CREATE INDEX ix_song_master_take_id ON song (master_take_id);
CREATE INDEX ix_song_owner_id ON song (owner_id);
CREATE INDEX ix_lyrics_version_deleted_at ON lyrics_version (deleted_at);
CREATE INDEX ix_lyrics_version_owner_id ON lyrics_version (owner_id);
CREATE INDEX ix_lyrics_version_parent_id ON lyrics_version (parent_id);
CREATE INDEX ix_lyrics_version_song_id ON lyrics_version (song_id);
CREATE INDEX ix_take_batch_id ON take (batch_id);
CREATE INDEX ix_take_deleted_at ON take (deleted_at);
CREATE INDEX ix_take_job_id ON take (job_id);
CREATE INDEX ix_take_lyrics_version_id ON take (lyrics_version_id);
CREATE INDEX ix_take_owner_id ON take (owner_id);
CREATE INDEX ix_take_root_id ON take (root_id);
CREATE INDEX ix_take_song_id ON take (song_id);
CREATE INDEX ix_lineage_edge_child_id ON lineage_edge (child_id);
CREATE INDEX ix_lineage_edge_deleted_at ON lineage_edge (deleted_at);
CREATE INDEX ix_lineage_edge_owner_id ON lineage_edge (owner_id);
CREATE INDEX ix_lineage_edge_parent_id ON lineage_edge (parent_id);
CREATE INDEX ix_asset_deleted_at ON asset (deleted_at);
CREATE INDEX ix_asset_owner_id ON asset (owner_id);
CREATE INDEX ix_asset_subject_id ON asset (subject_id);
CREATE INDEX ix_upload_deleted_at ON upload (deleted_at);
CREATE INDEX ix_upload_owner_id ON upload (owner_id);
CREATE INDEX ix_analysis_deleted_at ON analysis (deleted_at);
CREATE INDEX ix_analysis_lyrics_version_id ON analysis (lyrics_version_id);
CREATE INDEX ix_analysis_owner_id ON analysis (owner_id);
CREATE INDEX ix_analysis_take_id ON analysis (take_id);
CREATE INDEX ix_artwork_deleted_at ON artwork (deleted_at);
CREATE INDEX ix_artwork_job_id ON artwork (job_id);
CREATE INDEX ix_artwork_owner_id ON artwork (owner_id);
CREATE INDEX ix_artwork_song_id ON artwork (song_id);
CREATE INDEX ix_artwork_upload_id ON artwork (upload_id);
CREATE INDEX ix_character_deleted_at ON character (deleted_at);
CREATE INDEX ix_character_lora_asset_id ON character (lora_asset_id);
CREATE INDEX ix_character_owner_id ON character (owner_id);
CREATE INDEX ix_character_sheet_artwork_id ON character (sheet_artwork_id);
CREATE INDEX ix_character_ref_artwork_id ON character_ref (artwork_id);
CREATE INDEX ix_character_ref_character_id ON character_ref (character_id);
CREATE INDEX ix_character_ref_deleted_at ON character_ref (deleted_at);
CREATE INDEX ix_character_ref_owner_id ON character_ref (owner_id);
CREATE INDEX ix_character_ref_upload_id ON character_ref (upload_id);
CREATE INDEX ix_preset_deleted_at ON preset (deleted_at);
CREATE INDEX ix_preset_owner_id ON preset (owner_id);
CREATE INDEX ix_video_project_deleted_at ON video_project (deleted_at);
CREATE INDEX ix_video_project_owner_id ON video_project (owner_id);
CREATE INDEX ix_video_project_song_id ON video_project (song_id);
CREATE INDEX ix_video_project_take_id ON video_project (take_id);
CREATE INDEX ix_video_character_character_id ON video_character (character_id);
CREATE INDEX ix_video_character_deleted_at ON video_character (deleted_at);
CREATE INDEX ix_video_character_owner_id ON video_character (owner_id);
CREATE INDEX ix_video_character_video_project_id ON video_character (video_project_id);
CREATE INDEX ix_shot_current_version_id ON shot (current_version_id);
CREATE INDEX ix_shot_deleted_at ON shot (deleted_at);
CREATE INDEX ix_shot_owner_id ON shot (owner_id);
CREATE INDEX ix_shot_video_project_id ON shot (video_project_id);
CREATE INDEX ix_shot_version_clip_asset_id ON shot_version (clip_asset_id);
CREATE INDEX ix_shot_version_deleted_at ON shot_version (deleted_at);
CREATE INDEX ix_shot_version_job_id ON shot_version (job_id);
CREATE INDEX ix_shot_version_keyframe_asset_id ON shot_version (keyframe_asset_id);
CREATE INDEX ix_shot_version_owner_id ON shot_version (owner_id);
CREATE INDEX ix_shot_version_shot_id ON shot_version (shot_id);
CREATE INDEX ix_render_asset_id ON render (asset_id);
CREATE INDEX ix_render_deleted_at ON render (deleted_at);
CREATE INDEX ix_render_owner_id ON render (owner_id);
CREATE INDEX ix_render_video_project_id ON render (video_project_id);
CREATE INDEX ix_export_asset_id ON export (asset_id);
CREATE INDEX ix_export_deleted_at ON export (deleted_at);
CREATE INDEX ix_export_owner_id ON export (owner_id);
CREATE INDEX ix_export_song_id ON export (song_id);
CREATE INDEX ix_job_deleted_at ON job (deleted_at);
CREATE INDEX ix_job_owner_id ON job (owner_id);
CREATE INDEX ix_job_schedule ON job (lane, status, not_before);
CREATE INDEX ix_job_song_id ON job (song_id);
CREATE INDEX ix_job_dependency_deleted_at ON job_dependency (deleted_at);
CREATE INDEX ix_job_dependency_depends_on_job_id ON job_dependency (depends_on_job_id);
CREATE INDEX ix_job_dependency_job_id ON job_dependency (job_id);
CREATE INDEX ix_job_dependency_owner_id ON job_dependency (owner_id);
CREATE INDEX ix_setting_deleted_at ON setting (deleted_at);
CREATE INDEX ix_setting_owner_id ON setting (owner_id);
CREATE INDEX ix_provider_deleted_at ON provider (deleted_at);
CREATE INDEX ix_provider_owner_id ON provider (owner_id);

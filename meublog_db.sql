
CREATE TABLE reacao_usuario_post (
id_usuario integer,
id_post integer,
tipo_reacao varchar(50),
dt_reacao date,
PRIMARY KEY(id_usuario,id_post),
FOREIGN KEY(id_post) REFERENCES post (id_post)
);

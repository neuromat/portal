COPY experiments_classificationofdiseases(
  code,
  description, abbreviated_description,
  description_en, abbreviated_description_en,
  description_pt_br, abbreviated_description_pt_br)
FROM '<install_dir>/resources/cid-10.csv'
DELIMITER ','
CSV
HEADER;
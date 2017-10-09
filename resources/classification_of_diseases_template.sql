COPY experiments_classificationofdiseases(code, description, abbreviated_description) FROM
'<install_dir>/resources/icd10cm_order_2014.csv' DELIMITER
',' CSV HEADER;
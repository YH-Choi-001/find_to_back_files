DATETIME?="2025-09-15 00:00:00"

all: zip

files_edited_after_timestamp.txt: find_to_back_files.py
	python3 find_to_back_files.py --since $(DATETIME) > "files_edited_after_timestamp.txt"

relative_path_list.txt: files_edited_after_timestamp.txt
	grep -v "^\\[g\\]" "files_edited_after_timestamp.txt" | sed "s|/Users/yhchoi/Documents|.|g" > "relative_path_list.txt"

2b_zipped.txt: relative_path_list.txt
	awk '{print $$3}' < "relative_path_list.txt" > "2b_zipped.txt"

zip: 2b_zipped.txt
	tar -czvf ~/Documents_edited_since_$(DATETIME).tar.gz -L 2b_zipped.txt

clean:
	rm "files_edited_after_timestamp.txt" || true
	rm "relative_path_list.txt" || true
	rm "2b_zipped.txt" || true

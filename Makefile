DATETIME?="2025-09-15 00:00:00"

all: zip

files_edited_after_timestamp.txt: find_to_back_files.py
	python3 find_to_back_files.py --since $(DATETIME) > "files_edited_after_timestamp.txt"

relative_path_list.txt: files_edited_after_timestamp.txt
	sed "s|/Users/yhchoi/Documents|.|g" files_edited_after_timestamp.txt > "relative_path_list.txt"

zip_list.txt: relative_path_list.txt
	grep -v "^\\[g\\]" "relative_path_list.txt" | sed "s/^\[.*\] *[[:digit:]]* //g" > "zip_list.txt"

exclude_list.txt: relative_path_list.txt
	grep "^\\[g\\]" "relative_path_list.txt" | sed "s/^\[.*\] *[[:digit:]]* //g" > "exclude_list.txt"

zip: zip_list.txt exclude_list.txt
	cd ~/Documents && tar -czvf ~/Documents_edited_since_$(DATETIME).tar.gz -T "code/find_to_back_files/zip_list.txt" -X "code/find_to_back_files/exclude_list.txt"

clean:
	rm "files_edited_after_timestamp.txt" || true
	rm "relative_path_list.txt" || true
	rm "zip_list.txt" || true
	rm "exclude_list.txt" || true

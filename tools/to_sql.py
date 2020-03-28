import csv, json

def escape(row_index, string):
	try:
		string = string.encode().decode('cp1251').encode('utf8').decode('utf8');
	except:
		try:
			string = string.encode().decode('utf8').encode('utf8').decode('utf8');
		except:
			print("Unable to decode: ")
			print(string.encode())
			return ""
	return string

csv_path = "source.csv"
out_path = "autocompletion_lexemes.sql"
row_index = 0
batch_size = 300
batch = []
with open(out_path, "w", encoding="utf8") as  outfile:
	outfile.write("SET NAMES 'utf8' COLLATE 'utf8_general_ci';\n")
	with open(csv_path, "r") as f_obj:
		reader = csv.reader(f_obj)
		for row in reader:
			data = json.loads(row[0])
			lexeme_index = 0
			max_length = 0
			error = False
			for lexeme in data:
				max_length = max(max_length, len(lexeme))
			if (max_length < 100):
				for lexeme in data:
					escaped_lexeme = escape(row_index, lexeme).replace("\\", "\\\\").replace("\"", "\\\"")
					batch.append("(" + str(row_index) + "," + str(lexeme_index)  + ",\""  +  escaped_lexeme  + "\")")
					if (len(batch) >= batch_size):
						outfile.write("INSERT INTO `repository_autocompletion_lexemes` (ROW_ID, LEXEME_ID, TEXT) VALUES " + ",".join(batch)   + ";\n")
						batch = []
					lexeme_index = lexeme_index + 1
			row_index = row_index + 1
	if (len(batch) > 0):
		outfile.write("INSERT INTO `repository_autocompletion_lexemes` (ROW_ID, LEXEME_ID, TEXT) VALUES " + ",".join(batch)   + ";\n")
		batch = []
def process_file(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        lines = infile.readlines()
        
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break
            sentence = lines[i].strip()
            aspect = lines[i+1].strip()
            sentiment = lines[i+2].strip()
            sentence = sentence.replace("$T$", f'[B-ASP]{aspect}[E-ASP]')
            number_of_aspect_tokens = sentence.count('[B-ASP]')
            
            processed_sentence = f"{sentence} $LABEL$" + f" {sentiment}, " * number_of_aspect_tokens
            processed_sentence = processed_sentence[:-2]
            outfile.write(processed_sentence + "\n")

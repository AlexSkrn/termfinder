import argparse
import json
import os


def split_texts(texts, max_words=250):
    max_words = int(max_words)
    subtexts = []
    current_subtext = ''
    current_words = 0

    for text in texts:
        text_length_words = len(text.split())

        # Add the text to the current subtext and update the character count
        if current_subtext:
            current_subtext += '\n' + text
        else:
            current_subtext = text
        current_words += text_length_words

        # Check if the limit is exceeded after adding the new text
        if current_words > max_words:
            subtexts.append(current_subtext.strip())
            current_subtext = ''
            current_words = 0

    # Append the last subtext if not empty
    if current_subtext:
        subtexts.append(current_subtext.strip())

    return subtexts


def save_prompts(prompts_lst, requests_filename):
    with open(requests_filename, 'w', encoding='utf-8') as f:
        for prompt in prompts_lst:
            json_string = json.dumps(prompt)
            f.write(json_string + '\n')


def get_lines(source_filepath):
    source_list = []
    # count = 0
    with open(source_filepath, 'r', encoding='utf-8') as in_f:
        for line in in_f:
            line = line.strip()
            if line:
                # count += len(line)
                source_list.append(line)
    return source_list


def build_prompts(prompt_start, source_split, filename):
    prompts = [
        {   
            'prompt': prompt_start, 
            'text': text, 
            'source': filename
            } for text in source_split]
    return prompts


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source_filepath')
    parser.add_argument('--prompt_start')
    parser.add_argument('--max_words')
    parser.add_argument('--requests_filepath')
    args = parser.parse_args()

    files_lst = os.listdir(args.source_filepath)
    prompts_lst = []
    for f in files_lst:
        all_lines = get_lines(os.path.join(args.source_filepath, f))
        source_split = split_texts(all_lines, args.max_words)
        filename = os.path.basename(f)
        prompts = build_prompts(args.prompt_start, source_split, f)
        prompts_lst.extend(prompts)
    
    save_prompts(prompts_lst, args.requests_filepath)
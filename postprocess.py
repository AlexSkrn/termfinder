import argparse
import json
import re


def strip_punctuation(text):
    """
    # Example usage:
        text = "1. •  !!Hello, world!!"
        strip_punctuation(text)
        Hello, world
    """
    punctuation = """!"“”«»#$%&'()*+,-./:;<=>?@[\]^_`{|}~…\t\n"""  # ivxIVX
    punctuation += '1234567890' + ' '
    punctuation += '•·◦■□✓⁃'
    return text.strip(punctuation)


def find_substring_contexts(substring, larger_string):
    """
    # Example usage
    substring = 'health and safety standards'
    larger_string = 'Ensuring compliance with Health and Safety Standards is paramount for any organization. \
    By rigorously adhering to these health and safety standards, companies can prevent workplace injuries and \
    create a secure environment for their employees. Regular training and updates on health and safety standards \
    help maintain a culture of awareness and responsibility, fostering a proactive approach to potential hazards \
    and promoting overall well-being.'

    find_substring_contexts(substring, larger_string)
    ['Ensuring compliance with Health and Safety Standards is paramount for any organization. By r',
      'zation. By rigorously adhering to these health and safety standards, companies can prevent workplace injuri',
      'loyees. Regular training and updates on health and safety standards help maintain a culture of awareness an'
      ]
    """

    # Create a case insensitive pattern with the substring
    pattern = re.compile(re.escape(substring), re.IGNORECASE)

    matches = []
    for match in pattern.finditer(larger_string):
        start = max(match.start() - 40, 0)
        end = min(match.end() + 40, len(larger_string))
        context = larger_string[start:end]
        if context not in matches:
            matches.append(context)

    return matches


def read_responses(responses_filename):
    with open(responses_filename, 'r', encoding='utf-8') as from_f:
        text_responses = json.load(from_f)

    return text_responses


def read_requests(requests_filename):
    texts = []
    source_names = []
    with open(requests_filename, 'r', encoding='utf-8') as f:
        for line in f:
            prompt_dict = json.loads(line)
            texts.append(prompt_dict['text'])
            source_names.append(prompt_dict['source'])
    return texts, source_names


def get_unique_terms_context(requests, responses, filenames):
    """Return terms extracted by LLM plus their contexts
    from the corresponding text segments, plus filenames
    {'t1': {'contexts': [], 'filename': 'f1}}
    """
    terms_contexts_filenames_lst = []

    for i in range(len(responses)):
        terms = responses[i].split('\n')
        terms = [strip_punctuation(text) for text in terms]
        terms = [t for t in terms if t]
        terms = list(dict.fromkeys(terms))
        present_terms =[t for t in terms if t.lower() in requests[i].lower()]
        cased_terms = [change_case(t, requests[i]) for t in present_terms]
        terms_contexts_filenames = [(t, find_substring_contexts(t, requests[i]), filenames[i]) for t in cased_terms]
        # [[('t1', [matches], 'f1'), ('t2', [matches], 'f1'), ..., [...]]
        terms_contexts_filenames_lst.append(terms_contexts_filenames)

    # Keep only unique terms
    terms_contexts_filenames_uniq = {}
    for sub_list in terms_contexts_filenames_lst:
        for term_context_filename in sub_list:  # terms and their contents
            term = term_context_filename[0]
            contexts = term_context_filename[1]
            filename = term_context_filename[2]
            if term in terms_contexts_filenames_uniq.keys():
                if terms_contexts_filenames_uniq[term]['filename'] == filename:
                    # only keep the term's contexts for the first source file
                    # where the term is found
                    terms_contexts_filenames_uniq[term]['contexts'].extend(contexts)
            else:
                terms_contexts_filenames_uniq[term] = {'contexts': contexts, 'filename': filename}

    # make contexts unique
    for term in terms_contexts_filenames_uniq.keys():
        unique_contexts = list(set(terms_contexts_filenames_uniq[term]['contexts']))
        terms_contexts_filenames_uniq[term]['contexts'] = unique_contexts

    return terms_contexts_filenames_uniq


def write_unique_terms_contexts(terms_contexts_uniq, filename):
    with open(filename, 'w', encoding='utf-8') as to_f:
        json.dump(terms_contexts_uniq, to_f)


def change_case(term, context):
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    matches = []
    for m in pattern.finditer(context):
        matches.append(context[m.start():m.end()])
    return matches[-1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--responses_filename')
    parser.add_argument('--requests_filename')
    parser.add_argument('--terms_contexts_filename')
    args = parser.parse_args()


    responses = read_responses(args.responses_filename)
    requests, source_names = read_requests(args.requests_filename)
    terms_contexts_uniq = get_unique_terms_context(requests, responses, source_names) 
    write_unique_terms_contexts(terms_contexts_uniq, args.terms_contexts_filename)
    
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
    {'term': 'health and safety standards', 
     'contexts': ['Ensuring compliance with Health and Safety Standards is paramount for any organization. By r', 
                  'zation. By rigorously adhering to these health and safety standards, companies can prevent workplace injuri',
                  'loyees. Regular training and updates on health and safety standards help maintain a culture of awareness an'
                  ]
    }
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

    # Store the results in a dictionary
    result = {
        'term': substring,
        'contexts': matches,
        }
    return result


def read_responses(responses_filename):
    with open(responses_filename, 'r', encoding='utf-8') as from_f:
        text_responses = json.load(from_f)

    return text_responses


def read_requests(requests_filename):
    texts = []
    with open(requests_filename, 'r', encoding='utf-8') as f:
        for line in f:
            prompt_dict = json.loads(line)
            texts.append(prompt_dict['text'])
    return texts


def get_unique_terms_context(requests, responses):
    """Return terms extracted by chat plus their contexts 
    [{'term': 't1', 'contexts': [matches]}]
    from the corresponding text segment"""
    terms_contexts = []

    for i in range(len(responses)):
        terms = responses[i].split('\n')
        terms = [strip_punctuation(text) for text in terms]
        terms = [t for t in terms if t]
        terms = list(set(terms))
        terms = [t for t in terms if t.lower() in requests[i].lower()]
        terms = [find_substring_contexts(t, requests[i]) for t in terms]
        terms_contexts.append(terms)

    # Keep only unique terms and unique context (merge contexts)
    terms_contexts_uniq = {}
    for dict_elem in terms_contexts:
        for term_context in dict_elem:  # terms and their contents
            term = term_context['term']
            contexts = term_context['contexts']
            try:
                terms_contexts_uniq[term].extend(contexts)
            except KeyError:
                terms_contexts_uniq[term] = contexts

    # make contexts unique
    for key in terms_contexts_uniq.keys():
        terms_contexts_uniq[key] = list(set(terms_contexts_uniq[key]))

    return terms_contexts_uniq


def write_unique_terms_contexts(terms_contexts_uniq, filename):
    with open(filename, 'w', encoding='utf-8') as to_f:
        json.dump(terms_contexts_uniq, to_f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--responses_filename')
    parser.add_argument('--requests_filename')
    parser.add_argument('--terms_contexts_filename')
    args = parser.parse_args()


    responses = read_responses(args.responses_filename)
    requests = read_requests(args.requests_filename)
    terms_contexts_uniq = get_unique_terms_context(requests, responses) 
    write_unique_terms_contexts(terms_contexts_uniq, args.terms_contexts_filename)
    
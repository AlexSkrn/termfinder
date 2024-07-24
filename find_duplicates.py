import os
import argparse
import numpy as np
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def read_unique_terms_contexts(filename):
    with open(filename, 'r', encoding='utf-8') as from_f:
        unique_terms_contexts = json.load(from_f)
    return unique_terms_contexts

def load_extracted_terms(terms_contexts_uniq):
    terms = []
    terms_lower = []

    for term in terms_contexts_uniq.keys():
        terms.append(term)
        terms_lower.append(term.lower())

    return terms, terms_lower

def ngrams(text, n=2):
    """Return n-grams of a string."""
    text = re.sub(r'[“”",-./#!&()]|\s', r'', text)
    ngrams = zip(*[text[i:] for i in range(n)])
    return [''.join(ngram) for ngram in ngrams]

def get_internal_tf_idf_matrix(terms_lower):
    vectorizer = TfidfVectorizer(min_df=1, analyzer=ngrams)
    tf_idf_matrix = vectorizer.fit_transform(terms_lower)
    return tf_idf_matrix

def get_internal_similarities(tf_idf_matrix):
    return cosine_similarity(tf_idf_matrix)


def find_internal_duplicates(terms, cos_sim_table, cutoff_sim=0.99):
    threshold = 0.8  # below this value, (near-)duplicates are very rare

    range_to_search = cos_sim_table.shape[0]  # number of terms
    terms = np.array(terms)

    results = []
    for i in range(range_to_search):
        curr_term = terms[i]   # terms_df.loc[i]
        cond = (cos_sim_table[i][i+1:] > threshold)
        if np.sum(cond) >= 1:
            similar_ids = np.where(cond)[0] + (i + 1)  # get the indices of similar terms
            similar_vals = terms[similar_ids]
            similar_scores = cos_sim_table[i, similar_ids]
        # if sum(cond) >= 1:
        #     similar_ids = terms[i+1:][cond].index
        #     similar_vals = [v for v in terms[i+1:][cond].values]
        #     similar_scores = cos_sim_table[i][i+1:][cond]
            idx_max_score = np.argmax(similar_scores)  # index of max scoring duplicate
            max_score = similar_scores[idx_max_score]
            if max_score > cutoff_sim:  # this removes (near-)duplicates
                continue
            elif max_score > threshold:
                idx_sim_term = similar_ids[idx_max_score]
                sim_term = similar_vals[idx_max_score]
                line = f'{str(i)}\t{curr_term}\t{str(idx_sim_term)}\t{sim_term}\t{str(round(max_score, 3))}'
        else:
            line = f'{str(i)}\t{curr_term}'

        results.append(line)

    return results

def get_internal_duplicates(terms, cos_sim_table):
    internal_duplicates_results = []
    for cutoff_sim in [0.99, 0.9, 0.8]:
        results = find_internal_duplicates(
            terms=terms,   # df['term'],
            cos_sim_table=cos_sim_table,
            cutoff_sim=cutoff_sim
            )
        internal_duplicates_results.append(results)
    return internal_duplicates_results

def save_internal_duplicates(internal_duplicates, path):
    internal_paths = [
        '02_internal_candidate_duplicates_99_cutoff.txt',
        '02_internal_candidate_duplicates_90_cutoff.txt',
        '02_internal_candidate_duplicates_80_cutoff.txt'
        ]

    for file_name, results in zip(internal_paths, internal_duplicates):
        with open(os.path.join(path, file_name), 'w', encoding='utf-8') as to_f:
            for line in results:
                line = line + '\n'
                to_f.write(line)


def load_master_terms(master_terms_file):
    old_terms = []
    old_terms_cased = []
    with open(master_terms_file, 'r', encoding='utf-8') as from_f:
        for line in from_f:
            line = line.strip()
            if line:
                term = line.split('|')[0].strip()
                old_terms.append(term.lower().strip())
                old_terms_cased.append(line)
    return old_terms, old_terms_cased


def get_new_terms_lower(internal_duplicates):
    new_terms_lower = []
    for terms in internal_duplicates:
        terms_temp = []
        for line in terms:
            # _, term = line.strip().split('\t')
            term = line.strip().split('\t')[1]
            terms_temp.append(term.lower())
        new_terms_lower.append(terms_temp)
    return new_terms_lower

def compute_cosine_similarity_in_chunks(tf_idf_matrix, old_tf_idf_matrix, chunk_size=30_000):
    n_chunks = old_tf_idf_matrix.shape[0] // chunk_size + 1
    cos_sim_table = np.zeros((tf_idf_matrix.shape[0], old_tf_idf_matrix.shape[0]))

    for i in range(n_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, old_tf_idf_matrix.shape[0])
        old_tf_idf_chunk = old_tf_idf_matrix[start_idx:end_idx]

        cos_sim_chunk = cosine_similarity(tf_idf_matrix, old_tf_idf_chunk)
        cos_sim_table[:, start_idx:end_idx] = cos_sim_chunk

    return cos_sim_table


def find_duplicates_vs_master(results, cos_sim_table, cutoff_sim=0.99):
    # get similarities vs master into a structure to write a file
    threshold = 0.8  # below this value, (near-)duplicates are very rare
    results_vs_master = []
    for idx, line in enumerate(results):
        terms = line.strip().split('\t')
        if sum(cos_sim_table[idx] > threshold):
            idx_max_score = np.argmax(cos_sim_table[idx])
            max_score = round(cos_sim_table[idx][idx_max_score], 3)
            if max_score > cutoff_sim:  # this removes (near-)duplicates
                continue
            terms.insert(2, old_terms_cased[idx_max_score])
            terms.insert(3, str(max_score))
        else:
            terms.insert(2, '')
            terms.insert(3, '')
        new_line = '\t'.join(terms) + '\n'
        results_vs_master.append(new_line)
    return results_vs_master


def remove_newlines(context, replace_newline='¶'):
    """Clean context by replacing newlines and tabs."""
    return re.sub(r'[\n\t]', replace_newline, context)


def highlight_term(context, term, color='FFFF70'):
    simpletext = re.compile("(" + re.escape(term) + ")", re.IGNORECASE)
    replacement = f"<span style='background-color: #{color}'>\\1</span>"
    return re.sub(simpletext, replacement, context)


def highlight_all_terms(results_vs_master, terms_contexts_uniq, num_contexts=5):
    """Return list of html lines with highlihted terms in their contexts."""
    html_lines_lst = ["<table border='1'>", "<tr><th>Index</th><th>Term</th><th>Context</th></tr>"]
    for line in results_vs_master:
        idx = line.strip().split('\t')[0]
        term = line.strip().split('\t')[1]
        try:
            contexts = terms_contexts_uniq[term]  # get contexts for term
        except KeyError:
            continue
        new_line = f'{idx}\t{term}\t'
        context = remove_newlines(contexts[0])

        highlighted_context = highlight_term(context, term)
        html_lines_lst.append(f'<tr><td>{idx}</td><td>{term}</td><td>{highlighted_context}</td></tr>')

        new_line += f'{context}\n'
        if num_contexts > 1 and len(contexts) > 1:
            for context in contexts[1:num_contexts]:
                context = remove_newlines(context)
                new_line += f'\t\t{context}\n'

                highlighted_context = highlight_term(context, term)
                html_lines_lst.append(f'<tr><td> </td><td> </td><td>{highlighted_context}</td></tr>')
    html_lines_lst.append("</table>")

    return html_lines_lst


def add_header(results_vs_master):
    # final_results = []
    results_vs_master = results_vs_master.copy()
    max_length = 0
    for idx, line in enumerate(results_vs_master):
        terms = line.strip().split('\t')
        curr_length = len(terms) + 1
        if curr_length > max_length:
            max_length = curr_length
        # new_line = '\t'.join(terms) + '\n'  # why don't use input?
        # final_results.append(new_line)
    if max_length == 3:
        header = 'idx\tterm'
    else:
        header = 'idx\tterm\texisting_term_WBTerm\tsim_score'
    # decide if there are internal duplicates
    num_inter_duplicates = int((max_length - 5) / 3)
    # print(f'Num int dup: {num_inter_duplicates}')
    header_tail = '\tidx2\tinternal_duplicate\tsim_score' * num_inter_duplicates
    header += header_tail
    header += '\n'
    # print(f'max length: {max_length}')
    # print(header)
    # print(len(header.strip().split('\t')))
    # final_results.insert(0, header)  # why don't use input as is?
    results_vs_master.insert(0, header)
    return results_vs_master


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--terms_contexts_uniq_filename')
    parser.add_argument('--main_output_path')
    parser.add_argument('--sub_dir')
    parser.add_argument('--master_terms_filename')
    parser.add_argument('--number_contexts')

    args = parser.parse_args()
    
    # find internal duplicates
    terms_contexts_filename = args.terms_contexts_uniq_filename
    terms_contexts_uniq = read_unique_terms_contexts(terms_contexts_filename)
    terms, terms_lower = load_extracted_terms(terms_contexts_uniq)
    tf_idf_matrix = get_internal_tf_idf_matrix(terms_lower)
    cos_sim_table = get_internal_similarities(tf_idf_matrix)
    internal_duplicates = get_internal_duplicates(terms, cos_sim_table)
    save_internal_duplicates(internal_duplicates, args.sub_dir)

    # find duplicates vs master list
    old_terms, old_terms_cased = load_master_terms(args.master_terms_filename)
    vectorizer = TfidfVectorizer(min_df=1, analyzer=ngrams)
    old_tf_idf_matrix = vectorizer.fit_transform(old_terms)
 
    new_terms_lower = get_new_terms_lower(internal_duplicates)
    # vectorize new terms - this is list of lists
    tf_idf_matrices = []
    for terms in new_terms_lower:
        tf_idf_matrix = vectorizer.transform(terms)
        tf_idf_matrices.append(tf_idf_matrix)

    cos_sim_tables = []
    for tf_idf_matrix in tf_idf_matrices:
        cos_sim_table = compute_cosine_similarity_in_chunks(tf_idf_matrix, old_tf_idf_matrix)
        cos_sim_tables.append(cos_sim_table)

    vs_master = []
    for cutoff_sim, cos_sim_table, results in zip([0.99, 0.9, 0.8], cos_sim_tables, internal_duplicates):
        results_vs_master = find_duplicates_vs_master(
            results=results,
            cos_sim_table=cos_sim_table,
            cutoff_sim=cutoff_sim
            )
        vs_master.append(results_vs_master)

    vs_master_paths = [
    '03_candidate_duplicates_vs_master_99_cutoff.txt',
    '03_candidate_duplicates_vs_master_90_cutoff.txt',
    '03_candidate_duplicates_vs_master_80_cutoff.txt'
    ]

    for file_name, results in zip(vs_master_paths, vs_master):
        with open(os.path.join(args.sub_dir, file_name), 'w', encoding='utf-8') as to_f:
            for line in results:
                to_f.write(line)

    html_lines_to_write_lst = []

    for lines in vs_master:
        html_lines_to_write = highlight_all_terms(
            lines,
            terms_contexts_uniq,
            int(args.number_contexts)
            )
        html_lines_to_write_lst.append(html_lines_to_write)

    vs_master_paths = [
    'contexts_99_percent.html',
    'contexts_90_percent.html',
    'contexts_80_percent.html'
    ]

    for file_name, html_lines in zip(vs_master_paths, html_lines_to_write_lst):
        with open(os.path.join(args.main_output_path, file_name), 'w', encoding='utf-8') as to_f:
            for line in html_lines:
                to_f.write(f'{line}\n')

    results_with_headers = []
    for results in vs_master:
        results_with_headers.append(add_header(results))


    vs_master_paths_header = [
    'duplicates_99_percent.txt',
    'duplicates_90_percent.txt',
    'duplicates_80_percent.txt'
    ]

    for file_name, results in zip(vs_master_paths_header, results_with_headers):
        with open(os.path.join(args.main_output_path, file_name), 'w', encoding='utf-8') as to_f:
            for line in results:
                to_f.write(line)
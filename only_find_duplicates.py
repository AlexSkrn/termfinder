import argparse
from sklearn.feature_extraction.text import TfidfVectorizer

from find_duplicates import load_master_terms
from find_duplicates import get_internal_tf_idf_matrix
from find_duplicates import get_internal_similarities
from find_duplicates import find_internal_duplicates
from find_duplicates import ngrams
from find_duplicates import compute_cosine_similarity_in_chunks
from find_duplicates import find_duplicates_vs_master


def write_file(filepath, vs_master):
    with open(filepath, 'w', encoding='utf-8') as to_f:
        for line in vs_master:
            to_f.write(line)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--new_terms_filename')
    parser.add_argument('--master_terms_filename')
    parser.add_argument('--target_filepath')
    
    args = parser.parse_args()

    # internal duplicates
    new_terms_lower, new_terms_cased = load_master_terms(args.new_terms_filename)
    tf_idf_matrix = get_internal_tf_idf_matrix(new_terms_lower)
    cos_sim_table = get_internal_similarities(tf_idf_matrix)
    internal_duplicates = find_internal_duplicates(
        new_terms_cased,
        cos_sim_table,
        cutoff_sim=2  # keep all duplicates even 100%
        )
    
    # external duplicates
    old_terms_lower, old_terms_cased = load_master_terms(args.master_terms_filename)
    vectorizer = TfidfVectorizer(min_df=1, analyzer=ngrams)
    old_tf_idf_matrix = vectorizer.fit_transform(old_terms_lower)
    new_tf_idf_matrix = vectorizer.transform(new_terms_lower)
    new_vs_old_cos_sim_table = compute_cosine_similarity_in_chunks(
        new_tf_idf_matrix, 
        old_tf_idf_matrix
        )
    
    vs_master = find_duplicates_vs_master(
            results=internal_duplicates,
            cos_sim_table=new_vs_old_cos_sim_table,
            old_terms_cased=old_terms_cased,
            cutoff_sim=2  # keep all duplicates even 100%
            )
    
    write_file(args.target_filepath, vs_master)

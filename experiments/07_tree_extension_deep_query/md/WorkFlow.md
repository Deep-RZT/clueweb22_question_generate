# WorkFlow

## Feed a weblink / file sample (from Clueweb)

### Extract root keywords following a certain rubric as the final answer

1. Each keyword must be highly specific (e.g., proper nouns, numbers, technical terms).  
2. All keywords should be distinctive and not too broad or ambiguous.  
3. All keywords must be unique and not repeated.

### Generate a simple query. A root keyword is the only correct answer to the query

1. The query must based on the original doc (require a web search, not answerable by common sense)  
2. The query must have only one correct answer  
3. The query is solvable

## Feed the query to an answer verifier 

1. The question and its answer are fed to two independent LLM models. Each model will perform a validity and uniqueness check. The answer verifier will output True only if the query passes both model  
2. Keep the queries which meet the requirements

## Perform Series Extension and Parallel Extension

### Series extension

1. Extract n sub-keywords from query(q0) (where n is the minimal number of keywords sufficient to identify answer a0); keywords: k01, k02, ..., k0n
2. Perform Minimum Keyword Check: Each time a keyword is masked, check if the remaining keywords and descriptions can still pass the validity and uniqueness check  
3. a11 = k01, a12 = k02, a1n = k0n (Treat the extracted sub-keywords as the next generation of answers, denoted as a11, a12, ... a1n)  
4. For each answer, design a corresponding question (align with **Generate a simple query. A root keyword is the only correct answer to the query** based on 1-3 times search tool calls), denoted as q11 → a11, q12 → a12, q1n → a1n   
5. Perform Minimum Keyword Check and Validity and Uniqueness Check for each sub-question (q11 - q1n)   
6. Perform Shortcut Check: Ensure that each children question (q11, q12, ..., q1n) does not contain keywords that could directly pinpoint other ancestor answers. These new questions should only allow inference of their respective keyword answers (a11, a12, ..., a1n), and must not allow q11 to infer the answers to q12, q1n, etc. 
7. Combine q11, q12, ..., q1n and q0 to derive a final, deeply expanded question → q1 
8. Repeat steps 1-7 
9. After 2-3 rounds of iteration, obtain a final deep query.

### Parallel Extension

- To be fabricated

#### Comparative reasoning extension


## Trajectory Record (for validation by labor and agent training)

- The entire tree structure consists of all question-answer pairs from top to bottom, along with their respective hierarchical levels.



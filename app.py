import os
import threading
import time
from queue import Queue
from collections import Counter
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

def read_file_and_split(file_path, sectionsN):
    sections = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        text = file.read().lower()
        words = text.split()

    section_size = len(words) // sectionsN
    extra = len(words) % sectionsN
    
    start = 0
    for i in range(sectionsN):
        if i < extra:
            end = start + section_size + 1
        else:
            end = start + section_size
        sections.append(words[start:end])
        start = end

    return sections

def Map(section):
    return Counter(section)

def Reduce(mapped):
    return dict(mapped)

def Combiner(reduced_list):
    final_result = Counter()
    for data in reduced_list:
        final_result.update(data)
    return final_result

def process_section(section, reduced_list):
    mapped = Map(section)
    reduced = Reduce(mapped)
    reduced_list.append(reduced)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    sectionsN = int(request.form['threads'])
    file = request.files['datafile']
    filename = secure_filename(file.filename)
    file.save(filename)
    
    sections = read_file_and_split(filename, sectionsN)
    reduced_list = []
    threads = []

    start_time = time.time()

    for s in sections:
        thread = threading.Thread(target=process_section, args=(s, reduced_list))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    
    final_result = Combiner(reduced_list)

    execution_time = time.time() - start_time
    
    return jsonify({
        'result': dict(final_result),
        'execution_time': execution_time
    })

if __name__ == '__main__':
    app.run(debug=True)

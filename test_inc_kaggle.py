import tensorflow as tf
import sys
import os
import csv

# Disable tensorflow compilation warnings
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

'''
Classify images from test folder and predict dog breeds along with score.
'''

def fix_graph_def(graph_def):
        # fix nodes
        for node in graph_def.node:
            if node.op == 'RefSwitch':
                node.op = 'Switch'
                for index in range(len(node.input)):
                    if 'moving_' in node.input[index]:
                        node.input[index] = node.input[index] + '/read'
            elif node.op == 'AssignSub':
                node.op = 'Sub'
                if 'use_locking' in node.attr:
                    del node.attr['use_locking']
            if "dilations" in node.attr:
                del node.attr["dilations"]
            if "index_type" in node.attr:
                del node.attr["index_type"]

def classify_image(image_path, headers):
    f = open('submit.csv','w')
    writer = csv.DictWriter(f, fieldnames = headers)
    writer.writeheader()
    
    # Loads label file, strips off carriage return
    label_lines = [line.rstrip() for line
                   in tf.gfile.GFile("trained_model\\retrained_labels.txt")]
   
    # Unpersists graph from file
    
    with tf.gfile.FastGFile("kaggle\\trained_model\\output_graph.pb", 'rb') as f:
        graph_def = tf.GraphDef()
        #fix_graph_def(graph_def)
        graph_def.ParseFromString(f.read())
        _ = tf.import_graph_def(graph_def, name='')

    files = os.listdir(image_path)
    with tf.Session() as sess:
         for file in files:
             # Read the image_data
                image_data = tf.gfile.FastGFile(image_path+'\\'+file, 'rb').read()
                print ("Processing image",image_path+'\\'+file)
                # Feed the image_data as input to the graph and get first prediction
                softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')

                predictions = sess.run(softmax_tensor,  {'DecodeJpeg/contents:0': image_data}) 
                
                # Sort to show labels of first prediction in order of confidence
                top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
                records = []
                row_dict = {}
                head, tail = os.path.split(file)
                row_dict['id'] = tail.split('.')[0]
                max_prob=0
                max_str=""

                for node_id in top_k:
                    human_string = label_lines[node_id]

                    # Some breed names are mismatching with breed name in csv header names.
                    human_string = human_string.replace(" ","_")
                    if(human_string == 'german_short_haired_pointer'):
                        human_string = 'german_short-haired_pointer'
                    if(human_string == 'shih_tzu'):
                        human_string = 'shih-tzu'
                    if(human_string == 'wire_haired_fox_terrier'):
                        human_string = 'wire-haired_fox_terrier'
                    if(human_string == 'curly_coated_retriever'):
                        human_string = 'curly-coated_retriever'
                    if(human_string == 'black_and_tan_coonhound'):
                        human_string = 'black-and-tan_coonhound'
                    if(human_string == 'soft_coated_wheaten_terrier'):
                        human_string = 'soft-coated_wheaten_terrier'  
                    if(human_string == 'flat_coated_retriever'):
                        human_string = 'flat-coated_retriever'    
                    score = predictions[0][node_id]
                    if score > max_prob:
                        max_prob=score
                        max_str=human_string
                    #print('%s (score = %.5f)' % (human_string, score))
                    row_dict[human_string] = score
                print('%s (score = %.5f)' % (max_str, max_prob))
                records.append(row_dict.copy())
                writer.writerows(records)
    f.close()    

def main():
    test_data_folder = 'kaggle\\test'
    
    template_file = open('kaggle\\sample_submission.csv','r')
    d_reader = csv.DictReader(template_file)

    #get fieldnames from DictReader object and store in list
    headers = d_reader.fieldnames
    template_file.close()
    classify_image(test_data_folder, headers)
    

if __name__ == '__main__':
    main()

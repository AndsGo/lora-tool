import spacy

# 加载 spaCy 预训练模型
nlp = spacy.load("en_core_web_lg")

# 定义一个函数来检查标签是否与 "服装" 相关
def is_related(tag:str,reference_words:list[str]):
    # tag 中下划线变为 空格
    tag = tag.replace("_", " ")
    # 对标签进行分词和词性标注
    doc = nlp(tag)
    # 检查标签中的词是否与参考词相似，判断相识度是否大于0.5
    for token in doc:
        for reference_word in reference_words:
            reference_token = nlp(reference_word)[0]
            # 检查词向量是否为空
            if token.has_vector and reference_token.has_vector:
                similarity = token.similarity(reference_token)
                if similarity > 0.8:  # 可以根据需要调整阈值
                    # print(f"标签 '{tag}' 与 '{reference_word}' 相似，相似度为 {similarity}")
                    return True
    return False
# 定义一个函数，用于移除与服装相关的标签
# 参数 tags: 输入的标签列表，每个元素为字符串类型
# 参数 reference_words: 用于参考的与服装相关的单词列表
def remove_related_tags(tags:list[str],reference_words:list[str]):
    if not reference_words:
        return tags
    # 过滤服装类标签，使用列表推导式，保留那些与服装无关的标签
    filtered_tags = [tag for tag in tags if not is_related(tag,reference_words)]
    # 返回过滤后的标签列表
    return filtered_tags

# 判断两个词是否相似，相似度大于threshold，返回True，否则返回False
def is_similar(word1:str,word2:str,threshold:float=0.5):
    # 对标签进行分词和词性标注
    doc1 = nlp(word1)
    doc2 = nlp(word2)
    # 检查标签中的词是否与参考词相似，判断相识度是否大于threshold
    for token1 in doc1:
        for token2 in doc2:
            # 检查词向量是否为空
            if token1.has_vector and token2.has_vector:
                similarity = token1.similarity(token2)
                if similarity > threshold:  # 可以根据需要调整阈值
                    print(f"标签 '{word1}' 与 '{word2}' 相似，相似度为 {similarity}")
                    return True
    return False

# 判断词是否为名词
def is_noun(word:str):
    # 对标签进行分词和词性标注
    doc = nlp(word)
    # 检查标签中的词是否为名词，判断词性是否为名词
    for token in doc:
        if token.pos_ in ["NOUN","PROPN"]:
            return True
    return False
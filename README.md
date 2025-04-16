This project integrates a fine-tuned BERT model to classify user inquiries related to Taiwan's Labor Standards Act. Upon classification, the system retrieves predefined responses from a local dictionary, effectively simulating a legal chatbot. The architecture encompasses user input processing, BERT-based classification, and response generation.​

# 🤖 Taiwan Labor Law Chatbot Evaluation Report

## 🔖 Why this project matters：

This project demonstrates how LLMs can be grounded in real-world legal applications.
By fine-tuning BERT on Taiwan’s Labor Law categories, it empowers users to access statutory information more efficiently, promoting legal literacy and fairness in the workplace.

## 📄 Project Overview
This project evaluates the performance of two chatbot backend implementations for Taiwan Labor Law question answering:

1. **GPT + FAISS baseline retrieval**
2. **Fine-tuned BERT classifier + GPT hybrid**

Evaluation was conducted on a **50-question human-labeled test set**, and the accuracy of answers was manually annotated as:
- `1` = Correct
- `0` = Incorrect

---

## 🎯 Accuracy Comparison

| Model               | Accuracy  |
|---------------------|-----------|
| **BERT Fine-tuned** | **90%**   |
| GPT + FAISS         | **18%**   |

---

## 🔍 Insight Analysis

### 1. BERT Fine-tune Model
- Achieved **90% accuracy**, showing strong domain adaptation.
- Handles legal intent and category prediction with high consistency.
- Ideal for intent classification and grounding future chatbot responses.

### 2. GPT + FAISS Baseline
- Only **18% accuracy**, struggling with:
  - Ambiguous or implicit phrasing
  - Legal terminology variations
- Solely relying on semantic similarity is insufficient for legal use cases.

---

## 🔄 Suggested Architecture
- ✅ **Adopt BERT classifier as core routing engine**
- 🔄 Combine with GPT to generate fluent answers **after classification**
- 🔢 Future improvement: explore **multi-task learning** (classification + generation)

---

## 📋 Evaluation Dataset Summary
- **Number of questions:** 50
- **Annotation format:** CSV with columns: `question`, `answer`, `category`, `timestamp`, `label`
- **Label = 1** for correct, **0** for incorrect

---

## 📦 Repository
- Source Code: [AI_Chatbot Repository](https://github.com/HUEI-JYUN-DEBBY-YEH/AI_Chatbot)
- BERT Training Project: [BERT Fine-tune for Labor Law](https://github.com/HUEI-JYUN-DEBBY-YEH/bert-fine-tune-taiwan-labor-law)
- Deployed Demo: [BERT Fine-tune Chatbot on Render](https://bert-fine-tune.onrender.com)

---

## 🚀 Conclusion
> The fine-tuned BERT classifier significantly improves legal QA accuracy and is production-ready. GPT alone is insufficient for such high-precision applications. A hybrid approach is highly recommended for future iterations.

---

## 🌟 Author
- [@HUEI-JYUN-DEBBY-YEH](https://github.com/HUEI-JYUN-DEBBY-YEH)
- NLP Application Engineer in Training
- Focus: LLM, vector search, Flask API, multimodal, chatbot deployment

---

## 🔗 Related Links
- 📝 [Medium article: Building a Labor Law Legal Chatbot with BERT](https://medium.com/@debby.yeh1994)
- 📂 [Portfolio summary on Notion](https://mango-mapusaurus-5df.notion.site/Debby-Yeh-NLP-Application-Engineer-Portfolio-1ca5118474d2801caa58de564fb53e38?pvs=4)

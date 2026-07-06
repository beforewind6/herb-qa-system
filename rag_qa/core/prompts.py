# core/prompts.py
# 导入 PromptTemplate 类，用于创建 Prompt 模板
from langchain_core.prompts import PromptTemplate


# 定义 RAGPrompts 类，用于管理所有 Prompt 模板
class RAGPrompts:
    # 定义 RAG 提示模板
    # @: 装饰器， 注解(是给计算看的),注释(给码农看的)
    @staticmethod
    def rag_prompt():
        # 创建并返回 PromptTemplate 对象
        return PromptTemplate(
            template="""  
            你是一个IT领域的智能助手，帮助用户回答问题。你的语言专业，严谨，言简意赅。  
            如果提供了上下文，请基于上下文回答；如果没有上下文，请直接根据你的知识回答。  
            回答需要参考用户和系统的历史对话，如果没有历史对话，只参考上下文即可。
            如果答案来源于检索到的文档，请在回答中说明。

            上下文: 「 {context} 」
            问题: 「 {question} 」
            历史对话：「 {history} 」

            如果无法回答，请回复：“信息不足，无法回答，请联系人工客服，电话：{phone}。”  
            回答:  
            """,
            #   定义输入变量
            input_variables=["context", "question", "history", "phone"],
        )
        # @staticmethod

    # def rag_prompt():
    #     return PromptTemplate(
    #         template="""
    #     你是一个智能助手，负责帮助用户回答问题。请按照以下步骤处理：
    #
    #     1. **分析问题和上下文**：
    #        - 基于提供的上下文（如果有）和你的知识回答问题。
    #        - 如果答案来源于检索到的文档，请在回答中明确说明，例如：“根据提供的文档，……”。
    #
    #     2. **评估对话历史**：
    #        - 检查对话历史是否与当前问题相关（例如，是否涉及相同的话题、实体或问题背景）。
    #        - 如果对话历史与问题相关，请结合历史信息生成更准确的回答。
    #        - 如果对话历史无关（例如，仅包含问候或不相关的内容），忽略历史，仅基于上下文和问题回答。
    #
    #     3. **生成回答**：
    #        - 提供清晰、准确的回答，避免无关信息。
    #        - 如果上下文和历史消息均不足以回答问题，请回复：“信息不足，无法回答，请联系人工客服，电话：{phone}。”
    #
    #     **上下文**: {context}
    #     **对话历史**:
    #     {history}
    #     **问题**: {question}
    #
    #     **回答**:
    #     """,
    #         input_variables=["context", "history", "question", "phone"],
    #     )

    # 定义假设问题生成的 Prompt 模板
    @staticmethod
    def hyde_prompt():
        #   创建并返回 PromptTemplate 对象
        return PromptTemplate(
            template="""  
            假设你是用户，想了解以下问题，请生成一个简短的假设答案：  
            问题: 「 {query} 」  
            假设答案:  
            """,
            #   定义输入变量
            input_variables=["query"],
        )

    #   定义子查询生成的 Prompt 模板
    @staticmethod
    def subquery_prompt():
        #   创建并返回 PromptTemplate 对象
        return PromptTemplate(
            template="""  
            将以下复杂查询分解为多个简单子查询，每行一个子查询：  
            查询: 「 {query} 」  
            子查询:  
            """,
            #   定义输入变量
            input_variables=["query"],
        )

    #   定义回溯问题生成的 Prompt 模板
    @staticmethod
    def backtracking_prompt():
        #   创建并返回 PromptTemplate 对象
        return PromptTemplate(
            template="""  
            将以下复杂查询简化为一个更简单的问题：  
            查询: 「 {query} 」  
            简化问题:  
            """,
            #   定义输入变量
            input_variables=["query"],
        )


if __name__ == '__main__':
    prompt = RAGPrompts.hyde_prompt()
    prompt_str = prompt.format(query="大模型在教育领域的应用有哪些？")
    print(prompt_str)

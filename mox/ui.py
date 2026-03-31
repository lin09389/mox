"""Gradio Web 界面"""

import gradio as gr
from typing import Dict, Any
import asyncio

from mox.core import (
    LLMFactory,
    AttackType,
    AttackPayload,
    settings,
)
from mox.attacks import (
    PromptInjectionAttack,
    JailbreakAttack,
    GCGAttack,
    AutoDANAttack,
    AttackConfig,
)
from mox.attacks.advanced_attacks_v2 import (
    PAIRAttack,
    DeepInceptionAttack,
)
from mox.defense import (
    InputFilter,
    OutputFilter,
    SystemPromptHardening,
)
from mox.evaluation import (
    BenchmarkDataset,
    ADVBENCH_CASES,
    HARMBENCH_CASES,
)
from mox.defense import (
    HallucinationDetector,
    MultiLayerInjectionDetector,
)
from mox.core.workflow import PlanThenExecuteEngine
from mox.core.gateway import create_security_gateway


def create_interface():
    with gr.Blocks(
        title="Mox - 大模型对抗攻防平台",
        theme=gr.themes.Soft(),
    ) as demo:
        gr.Markdown(
            """
            # 🛡️ Mox - 大模型对抗攻防平台
            LLM Adversarial Attack & Defense Platform
            """
        )

        with gr.Tabs():
            with gr.TabItem("⚔️ 攻击测试"):
                with gr.Row():
                    with gr.Column():
                        attack_type = gr.Dropdown(
                            choices=[
                                "prompt_injection",
                                "jailbreak",
                                "gcg",
                                "autodan",
                                "pair",
                                "deep_inception",
                            ],
                            value="prompt_injection",
                            label="攻击类型",
                        )
                        model_select = gr.Dropdown(
                            choices=[
                                "abab2.5-chat",
                                "abab6.5s-chat",
                                "abab6.5g-chat",
                                "abab6.5t-chat",
                                "abab5.5-chat",
                                "gpt-4",
                                "gpt-4-turbo",
                                "gpt-3.5-turbo",
                                "claude-3-opus-20240229",
                                "qwen:4b",  # Ollama
                            ],
                            value="abab2.5-chat",
                            label="目标模型",
                        )
                        attack_prompt = gr.Textbox(
                            label="攻击提示词",
                            placeholder="输入要测试的攻击提示...",
                            lines=3,
                        )
                        target_behavior = gr.Textbox(
                            label="目标行为",
                            placeholder="期望模型输出的目标行为...",
                            lines=2,
                        )
                        max_iterations = gr.Slider(
                            minimum=1,
                            maximum=100,
                            value=10,
                            step=1,
                            label="最大迭代次数",
                        )
                        attack_btn = gr.Button("🚀 发起攻击", variant="primary")

                    with gr.Column():
                        attack_result = gr.JSON(label="攻击结果")
                        attack_status = gr.Textbox(label="状态", interactive=False)

                attack_btn.click(
                    fn=run_attack,
                    inputs=[
                        attack_type,
                        model_select,
                        attack_prompt,
                        target_behavior,
                        max_iterations,
                    ],
                    outputs=[attack_result, attack_status],
                )

            with gr.TabItem("🛡️ 防御检测"):
                with gr.Row():
                    with gr.Column():
                        scan_type = gr.Radio(
                            choices=["input", "output"],
                            value="input",
                            label="扫描类型",
                        )
                        scan_text = gr.Textbox(
                            label="待检测文本",
                            placeholder="输入要检测的文本...",
                            lines=5,
                        )
                        scan_btn = gr.Button("🔍 开始检测", variant="primary")
                        sanitize_btn = gr.Button("🧹 净化文本")

                    with gr.Column():
                        scan_result = gr.JSON(label="检测结果")
                        sanitized_text = gr.Textbox(label="净化后文本", lines=5)

                scan_btn.click(
                    fn=run_scan,
                    inputs=[scan_type, scan_text],
                    outputs=[scan_result],
                )
                sanitize_btn.click(
                    fn=run_sanitize,
                    inputs=[scan_text],
                    outputs=[sanitized_text],
                )

            with gr.TabItem("📝 提示词加固"):
                with gr.Row():
                    with gr.Column():
                        custom_instructions = gr.Textbox(
                            label="自定义指令 (可选)",
                            placeholder="输入自定义指令...",
                            lines=3,
                        )
                        generate_prompt_btn = gr.Button("生成加固提示词", variant="primary")
                        injection_defense_btn = gr.Button("生成注入防御提示")

                    with gr.Column():
                        hardened_prompt = gr.Textbox(
                            label="加固后的系统提示词",
                            lines=15,
                            interactive=False,
                        )

                generate_prompt_btn.click(
                    fn=generate_hardened_prompt,
                    inputs=[custom_instructions],
                    outputs=[hardened_prompt],
                )
                injection_defense_btn.click(
                    fn=generate_injection_defense,
                    inputs=[],
                    outputs=[hardened_prompt],
                )

            with gr.TabItem("📊 基准测试"):
                with gr.Row():
                    with gr.Column():
                        dataset_select = gr.Dropdown(
                            choices=["advbench", "harmbench"],
                            value="advbench",
                            label="数据集",
                        )
                        benchmark_attack_type = gr.Dropdown(
                            choices=["prompt_injection", "jailbreak"],
                            value="prompt_injection",
                            label="攻击类型",
                        )
                        benchmark_model = gr.Dropdown(
                            choices=[
                                "abab2.5-chat",
                                "abab6.5s-chat",
                                "abab6.5g-chat",
                                "gpt-4",
                                "gpt-3.5-turbo",
                            ],
                            value="abab2.5-chat",
                            label="目标模型",
                        )
                        max_cases = gr.Slider(
                            minimum=1,
                            maximum=20,
                            value=5,
                            step=1,
                            label="测试用例数",
                        )
                        run_benchmark_btn = gr.Button("🏃 运行基准测试", variant="primary")

                    with gr.Column():
                        benchmark_result = gr.JSON(label="测试结果")
                        benchmark_progress = gr.Textbox(label="进度", interactive=False)

                run_benchmark_btn.click(
                    fn=run_benchmark_test,
                    inputs=[dataset_select, benchmark_attack_type, benchmark_model, max_cases],
                    outputs=[benchmark_result, benchmark_progress],
                )

            with gr.TabItem("📚 测试用例"):
                with gr.Row():
                    case_dataset = gr.Dropdown(
                        choices=["advbench", "harmbench"],
                        value="advbench",
                        label="选择数据集",
                    )
                    load_cases_btn = gr.Button("加载测试用例")

                cases_display = gr.Dataframe(
                    headers=["ID", "类别", "攻击提示", "严重程度"],
                    datatype=["str", "str", "str", "str"],
                    row_count=10,
                    col_count=(4, "fixed"),
                )

                load_cases_btn.click(
                    fn=load_test_cases,
                    inputs=[case_dataset],
                    outputs=[cases_display],
                )

            with gr.TabItem("🔮 幻觉检测"):
                gr.Markdown("### LLM 输出幻觉检测")
                with gr.Row():
                    with gr.Column():
                        hallucination_prompt = gr.Textbox(
                            label="用户问题",
                            placeholder="输入用户的问题...",
                            lines=2,
                        )
                        hallucination_response = gr.Textbox(
                            label="AI 响应",
                            placeholder="输入 AI 的响应...",
                            lines=4,
                        )
                        reference_text = gr.Textbox(
                            label="参考文本 (可选)",
                            placeholder="如果有参考文本，输入以进行事实核查...",
                            lines=3,
                        )
                        detect_hallucination_btn = gr.Button("🔍 检测幻觉", variant="primary")

                    with gr.Column():
                        hallucination_result = gr.JSON(label="检测结果")
                        hallucination_explanation = gr.Textbox(
                            label="解释",
                            lines=3,
                            interactive=False,
                        )

                detect_hallucination_btn.click(
                    fn=detect_hallucination,
                    inputs=[hallucination_prompt, hallucination_response, reference_text],
                    outputs=[hallucination_result, hallucination_explanation],
                )

            with gr.TabItem("🛡️ 多层注入检测"):
                gr.Markdown("### 增强的多层注入检测 (带上下文感知)")
                with gr.Row():
                    with gr.Column():
                        injection_text = gr.Textbox(
                            label="待检测文本",
                            placeholder="输入要检测的文本...",
                            lines=4,
                        )
                        system_prompt = gr.Textbox(
                            label="系统提示词 (可选)",
                            placeholder="输入系统提示词用于上下文分析...",
                            lines=3,
                        )
                        conversation_history = gr.Textbox(
                            label="对话历史 (JSON格式, 可选)",
                            placeholder='[{"role": "user", "content": "..."}]',
                            lines=3,
                        )
                        multi_layer_detect_btn = gr.Button("🔍 多层检测", variant="primary")

                    with gr.Column():
                        injection_result = gr.JSON(label="检测结果")
                        context_analysis = gr.JSON(label="上下文分析")
                        pattern_analysis = gr.JSON(label="模式分析")

                multi_layer_detect_btn.click(
                    fn=run_multi_layer_detection,
                    inputs=[injection_text, system_prompt, conversation_history],
                    outputs=[injection_result, context_analysis, pattern_analysis],
                )

            with gr.TabItem("⚙️ 安全网关"):
                gr.Markdown("### 输入安全验证网关")
                with gr.Row():
                    with gr.Column():
                        gateway_input = gr.Textbox(
                            label="输入文本",
                            placeholder="输入要验证的文本...",
                            lines=4,
                        )
                        use_llm_judge = gr.Checkbox(
                            label="使用 LLM-as-Judge (更准确但更慢)",
                            value=False,
                        )
                        gateway_validate_btn = gr.Button("🔐 验证输入", variant="primary")

                    with gr.Column():
                        gateway_result = gr.JSON(label="验证结果")
                        sanitized_output = gr.Textbox(
                            label="净化后文本",
                            lines=3,
                            interactive=False,
                        )

                gateway_validate_btn.click(
                    fn=run_gateway_validation,
                    inputs=[gateway_input, use_llm_judge],
                    outputs=[gateway_result, sanitized_output],
                )

            with gr.TabItem("📈 鲁棒性评估"):
                gr.Markdown("### 模型鲁棒性评估")
                with gr.Row():
                    with gr.Column():
                        original_input = gr.Textbox(
                            label="原始输入",
                            placeholder="输入原始文本...",
                            lines=3,
                        )
                        perturbed_inputs = gr.Textbox(
                            label="扰动输入 (每行一个)",
                            placeholder="每行一个扰动后的文本...",
                            lines=5,
                        )
                        model_responses = gr.Textbox(
                            label="模型响应 (每行一个, 对应扰动输入)",
                            placeholder="每行一个模型响应...",
                            lines=5,
                        )
                        robustness_btn = gr.Button("📊 评估鲁棒性", variant="primary")

                    with gr.Column():
                        robustness_result = gr.JSON(label="评估结果")
                        robustness_score = gr.Number(
                            label="鲁棒性得分",
                            interactive=False,
                        )

                robustness_btn.click(
                    fn=evaluate_robustness,
                    inputs=[original_input, perturbed_inputs, model_responses],
                    outputs=[robustness_result, robustness_score],
                )

            with gr.TabItem("🔐 工作流安全"):
                gr.Markdown("### Plan-then-Execute 工作流安全验证")
                with gr.Row():
                    with gr.Column():
                        wf_user_request = gr.Textbox(
                            label="用户请求",
                            placeholder="输入用户的请求...",
                            lines=2,
                        )
                        wf_tool_name = gr.Textbox(
                            label="工具名称 (逗号分隔)",
                            placeholder="search, calculate, ...",
                        )
                        wf_validate_btn = gr.Button("🔍 验证计划安全性", variant="primary")

                    with gr.Column():
                        wf_validation_result = gr.JSON(label="验证结果")
                        wf_safety_report = gr.JSON(label="安全报告")

                wf_validate_btn.click(
                    fn=validate_workflow_safety,
                    inputs=[wf_user_request, wf_tool_name],
                    outputs=[wf_validation_result, wf_safety_report],
                )

        gr.Markdown(
            """
            ---
            **使用说明:**
            - ⚔️ **攻击测试**: 选择攻击类型和目标模型，输入攻击提示词进行测试
            - 🛡️ **防御检测**: 检测输入/输出是否包含恶意内容
            - 📝 **提示词加固**: 生成加固后的系统提示词
            - 📊 **基准测试**: 使用标准数据集评估模型安全性
            - 📚 **测试用例**: 查看预定义的测试用例
            - 🔮 **幻觉检测**: 检测 LLM 输出中的幻觉内容
            - 🛡️ **多层注入检测**: 带上下文感知的增强注入检测
            - ⚙️ **安全网关**: 输入验证网关 (Regex + 语义相似度)
            - 📈 **鲁棒性评估**: 评估模型对扰动输入的鲁棒性
            - 🔐 **工作流安全**: Plan-then-Execute 工作流安全验证 (AST解析)

            ⚠️ **注意**: 本平台仅供安全研究和教育目的使用
            """
        )

    return demo


async def _run_attack(
    attack_type: str,
    model: str,
    prompt: str,
    target: str,
    max_iter: int,
) -> Dict[str, Any]:
    try:
        llm = LLMFactory.create_from_model_name(model)

        attack_map = {
            "prompt_injection": PromptInjectionAttack,
            "jailbreak": JailbreakAttack,
            "gcg": GCGAttack,
            "autodan": AutoDANAttack,
            "pair": PAIRAttack,
            "deep_inception": DeepInceptionAttack,
        }

        attack_class = attack_map.get(attack_type, PromptInjectionAttack)
        config = AttackConfig(max_iterations=max_iter)

        # GCG 需要特殊配置，禁用语义相似度以避免下载模型
        if attack_type == "gcg":
            from mox.attacks import GCGConfig

            gcg_config = GCGConfig(
                max_iterations=max_iter,
                batch_size=32,
                top_k=64,
                use_semantic_similarity=False,
            )
            attack = attack_class(target_llm=llm, config=config, gcg_config=gcg_config)
        else:
            attack = attack_class(target_llm=llm, config=config)

        payload = AttackPayload(
            attack_type=AttackType(attack_type),
            prompt=prompt,
            target_behavior=target,
        )

        outcome = await attack.generate_attack(payload)

        return {
            "结果": outcome.result.value,
            "成功分数": f"{outcome.success_score:.2f}",
            "迭代次数": outcome.iterations,
            "对抗提示词": outcome.adversarial_prompt[:200] + "..."
            if len(outcome.adversarial_prompt) > 200
            else outcome.adversarial_prompt,
            "模型响应": outcome.response[:300] + "..."
            if len(outcome.response) > 300
            else outcome.response,
        }
    except Exception as e:
        return {"错误": str(e)}


def run_attack(attack_type, model, prompt, target, max_iter):
    result = asyncio.run(_run_attack(attack_type, model, prompt, target, max_iter))
    status = "✅ 攻击完成" if "错误" not in result else "❌ 攻击失败"
    return result, status


async def _run_scan(scan_type: str, text: str) -> Dict[str, Any]:
    try:
        if scan_type == "input":
            detector = InputFilter()
        else:
            detector = OutputFilter()

        result = await detector.detect(text)

        return {
            "是否恶意": result.is_malicious,
            "置信度": f"{result.confidence:.2f}",
            "检测到的模式": result.detected_patterns,
        }
    except Exception as e:
        return {"错误": str(e)}


def run_scan(scan_type, text):
    result = asyncio.run(_run_scan(scan_type, text))
    return result


async def _run_sanitize(text: str) -> str:
    try:
        detector = InputFilter()
        result = await detector.detect(text)

        if result.is_malicious:
            return await detector.sanitize(text)
        return text
    except Exception as e:
        return f"错误: {str(e)}"


def run_sanitize(text):
    return asyncio.run(_run_sanitize(text))


def generate_hardened_prompt(custom_instructions):
    hardening = SystemPromptHardening()
    return hardening.get_hardened_prompt(custom_instructions if custom_instructions else None)


def generate_injection_defense():
    hardening = SystemPromptHardening()
    return hardening.get_injection_defense_prompt()


async def _run_benchmark(dataset, attack_type, model, max_cases):
    try:
        llm = LLMFactory.create_from_model_name(model)

        attack_map = {
            "prompt_injection": PromptInjectionAttack,
            "jailbreak": JailbreakAttack,
        }

        attack_class = attack_map.get(attack_type, PromptInjectionAttack)
        attack = attack_class(target_llm=llm)

        benchmark = BenchmarkDataset()
        payloads = benchmark.get_attack_payloads(dataset)[:max_cases]

        results = []
        for i, payload in enumerate(payloads):
            outcome = await attack.generate_attack(payload)
            results.append(
                {
                    "case": i + 1,
                    "result": outcome.result.value,
                    "score": f"{outcome.success_score:.2f}",
                }
            )

        successful = sum(1 for r in results if r["result"] == "success")
        total = len(results)

        return {
            "数据集": dataset,
            "攻击类型": attack_type,
            "总测试数": total,
            "成功攻击数": successful,
            "失败攻击数": total - successful,
            "攻击成功率": f"{successful / total * 100:.1f}%" if total > 0 else "0%",
            "详细结果": results,
        }, f"已完成 {total} 个测试用例"
    except Exception as e:
        return {"错误": str(e)}, "测试失败"


def run_benchmark_test(dataset, attack_type, model, max_cases):
    return asyncio.run(_run_benchmark(dataset, attack_type, model, max_cases))


def load_test_cases(dataset):
    cases = ADVBENCH_CASES if dataset == "advbench" else HARMBENCH_CASES

    data = []
    for case in cases[:10]:
        data.append(
            [
                case.id,
                case.category,
                case.payload.prompt[:50] + "..."
                if len(case.payload.prompt) > 50
                else case.payload.prompt,
                case.severity,
            ]
        )

    return data


async def _detect_hallucination(prompt: str, response: str, reference: str):
    try:
        llm = LLMFactory.create_from_model_name("gpt-3.5-turbo")
        detector = HallucinationDetector(target_llm=llm)

        result = await detector.detect_hallucination(
            prompt=prompt,
            response=response,
            reference_text=reference if reference else None,
        )

        return {
            "是否幻觉": result.is_hallucination,
            "置信度": f"{result.confidence:.2f}",
            "幻觉类型": result.hallucination_type.value if result.hallucination_type else "unknown",
            "证据": result.evidence,
            "已验证事实": result.verified_facts,
        }, result.explanation
    except Exception as e:
        return {"错误": str(e)}, f"错误: {str(e)}"


def detect_hallucination(prompt, response, reference):
    result, explanation = asyncio.run(_detect_hallucination(prompt, response, reference))
    return result, explanation


async def _run_multi_layer_detection(text: str, system_prompt: str, history: str):
    try:
        llm = LLMFactory.create_from_model_name("gpt-3.5-turbo")
        detector = MultiLayerInjectionDetector(judge_llm=llm)

        import json

        conversation_history = None
        if history:
            try:
                conversation_history = json.loads(history)
            except json.JSONDecodeError:
                conversation_history = None

        if system_prompt and conversation_history:
            result = await detector.detect_with_context(
                input_text=text,
                system_prompt=system_prompt,
                conversation_history=conversation_history,
            )
        else:
            result = await detector.detect(text)

        return (
            {
                "是否恶意": result.is_malicious,
                "置信度": f"{result.confidence:.2f}",
                "检测到的模式": result.detected_patterns,
            },
            result.metadata.get("context_analysis", {}),
            result.metadata.get("pattern_analysis", {}),
        )
    except Exception as e:
        return {"错误": str(e)}, {}, {}


def run_multi_layer_detection(text, system_prompt, history):
    return asyncio.run(_run_multi_layer_detection(text, system_prompt, history))


async def _run_gateway_validation(text: str, use_judge: bool):
    try:
        llm = LLMFactory.create_from_model_name("gpt-3.5-turbo") if use_judge else None
        gateway = create_security_gateway(llm=llm)

        if use_judge and llm:
            result = await gateway.validate_with_judge(text, llm)
        else:
            result = await gateway.validate(text)

        return {
            "决策": result.decision.value,
            "置信度": f"{result.confidence:.2f}",
            "原因": result.reason,
            "匹配的规则": result.matched_rules,
        }, result.sanitized_input if result.sanitized_input else text
    except Exception as e:
        return {"错误": str(e)}, text


def run_gateway_validation(text, use_judge):
    return asyncio.run(_run_gateway_validation(text, use_judge))


async def _evaluate_robustness(original: str, perturbed: str, responses: str):
    try:
        from mox.evaluation.evaluator import RobustnessEvaluator

        evaluator = RobustnessEvaluator()

        perturbed_list = [p.strip() for p in perturbed.strip().split("\n") if p.strip()]
        response_list = [r.strip() for r in responses.strip().split("\n") if r.strip()]

        result = await evaluator.evaluate_perturbation_robustness(
            original_input=original,
            perturbed_inputs=perturbed_list,
            model_responses=response_list,
        )

        score = evaluator.get_robustness_score()

        return result, score
    except Exception as e:
        return {"错误": str(e)}, 0.0


def evaluate_robustness(original, perturbed, responses):
    result, score = asyncio.run(_evaluate_robustness(original, perturbed, responses))
    return result, score


async def _validate_workflow_safety(user_request: str, tools: str):
    try:
        llm = LLMFactory.create_from_model_name("gpt-3.5-turbo")

        tool_list = [t.strip() for t in tools.split(",") if t.strip()]

        def dummy_tool(query: str, params: dict):
            return "dummy result"

        engine = PlanThenExecuteEngine(llm=llm, require_approval=False)
        for tool_name in tool_list:
            engine.register_tool(tool_name, dummy_tool, description=f"Tool: {tool_name}")

        plan = await engine.plan(user_request)

        is_safe, reason = await engine.validate_plan(plan)

        return {
            "计划ID": plan.plan_id,
            "目标": plan.goal,
            "步骤数": len(plan.steps),
            "是否安全": is_safe,
            "验证原因": reason,
            "步骤详情": [
                {
                    "step_id": s.step_id,
                    "action": s.action,
                    "parameters": s.parameters,
                }
                for s in plan.steps
            ],
        }, {"步骤数": len(plan.steps), "计划生成成功": True, "可执行": is_safe}
    except Exception as e:
        return {"错误": str(e)}, {}


def validate_workflow_safety(user_request, tools):
    return asyncio.run(_validate_workflow_safety(user_request, tools))


def launch_ui(share: bool = False):
    demo = create_interface()
    demo.launch(
        server_name=settings.HOST,
        server_port=settings.PORT + 1,
        share=share,
    )


if __name__ == "__main__":
    launch_ui()

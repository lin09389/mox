import sys
content = open('mox/attacks/gcg.py', 'r', encoding='utf-8').read()

fixed = '''
            if self.gcg_config.verbose and iteration % 10 == 0:
                print(
                    f"Iteration {iteration}: Best score = {best_score:.4f}, Elite candidates = {len(elite_candidates)}"
                )

        result = (
            AttackResult.SUCCESS
            if best_score >= self.config.success_threshold
            else AttackResult.FAILURE
        )

        return self._create_outcome(
            result=result,
            original_prompt=payload.prompt,
            adversarial_prompt=f"{payload.prompt} {best_suffix}",
            model_response=best_response,
            iterations=self.gcg_config.max_iterations,
            success_score=best_score,
            metadata={"method": "gcg++"},
        )

    async def _compute_gradient_info(self, prompt: str, target: str) -> "Optional[torch.Tensor]":
        try:
            if self._victim_model is None or self._tokenizer is None:
                return None

            inputs = self._tokenizer(prompt, return_tensors="pt")

            with torch.no_grad():
                outputs = self._victim_model(**inputs)
                logits = outputs.logits[0, -1, :]

            target_ids = self._tokenizer.encode(target, add_special_tokens=False)
            if target_ids:
                target_id = target_ids[0]
                logits_at_target = logits[target_id]
            else:
                logits_at_target = logits.max()

            importance = torch.softmax(logits, dim=-1) * torch.abs(logits - logits_at_target)

            return importance

        except Exception as e:
            logger.debug(f"Gradient computation failed: {e}")
            return None

    def _gradient_guided_mutate(self, suffix: str, gradient_info: "Optional[torch.Tensor]") -> str:
'''

lines = content.split('\n')
idx = 0
for i, line in enumerate(lines):
    if 'if self.gcg_config.verbose and iteration % 10 == 0:' in line and 'elite_candidates' not in lines[i+1]:
        idx = i
        break

if idx == 0:
    for i, line in enumerate(lines):
        if 'if self.gcg_config.verbose and iteration % 10 == 0:' in line:
            idx = i

start_lines = lines[:idx]
end_idx = 0
for i in range(idx, len(lines)):
    if 'def _gradient_guided_mutate' in lines[i]:
        end_idx = i + 1
        break

end_lines = lines[end_idx:]

with open('mox/attacks/gcg.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(start_lines) + '\n' + fixed.strip('\n') + '\n' + '\n'.join(end_lines))

from crewai_tools import BaseTool

class TrustworthinessAlgorithmTool(BaseTool):
    name: str = "Trustworthiness Algorithm Tool"
    description: str = "Calculate the trustworthiness score for a person based on their statements."

    def _run(self, statements: list) -> dict:
        """Calculate the trustworthiness score for a person."""
        try:
            # This is a placeholder for a more sophisticated algorithm.
            # In a real implementation, you would use a more advanced algorithm
            # that takes into account the context of the statements, the source of the information,
            # and other factors.
            
            num_true = 0
            num_false = 0
            
            for statement in statements:
                if statement['verdict'] == 'true':
                    num_true += 1
                elif statement['verdict'] == 'false':
                    num_false += 1
            
            if num_true + num_false == 0:
                trustworthiness_score = 0.5 # Neutral score
            else:
                trustworthiness_score = num_true / (num_true + num_false)
            
            return {
                'status': 'success',
                'trustworthiness_score': trustworthiness_score,
                'num_true': num_true,
                'num_false': num_false
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

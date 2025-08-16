                    if condition_met and "then_workflow" in params:
                        then_workflow_def = params["then_workflow"]
                        then_steps = [WorkflowStep(**s) for s in then_workflow_def["steps"]]
                        temp_workflow = Workflow(name=f"{workflow_name}_then", steps=then_steps)
                        sub_state = await self._run_sub_workflow(temp_workflow, workflow_state)
                        workflow_state.update(sub_state)
                    elif not condition_met and "else_workflow" in params:
                        else_workflow_def = params["else_workflow"]
                        else_steps = [WorkflowStep(**s) for s in else_workflow_def["steps"]]
                        temp_workflow = Workflow(name=f"{workflow_name}_else", steps=else_steps)
                        sub_state = await self._run_sub_workflow(temp_workflow, workflow_state)
                        workflow_state.update(sub_state)
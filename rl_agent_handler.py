from rs.machine.handlers.handler import Handler
from rs.machine.state import GameState
from rs.machine.command import Command

class RLAgentHandler(Handler):
    """
    A handler that wraps the RLAgent, allowing it to make decisions within the game loop.
    """
    def __init__(self, agent):
        self.agent = agent

    def can_handle(self, state: GameState) -> bool:
        """
        This handler can act whenever the game is in combat and there are choices to be made.
        """
        # The AI should only act during combat when it's the player's turn.
        return state.is_in_combat() and state.has_choice("play")

    def handle(self, state: GameState) -> Command:
        """
        Gets the AI's chosen action and returns it as a command.
        """
        # Get the full game state dictionary needed for vectorization
        game_state_dict = state.game_state()
        # Ask the agent to choose an action based on the current state
        action_command = self.agent.choose_action(game_state_dict)
        # Return the chosen command to the game loop
        return Command(commands=[action_command])
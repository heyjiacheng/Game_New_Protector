# Swedish City Sustainability Game

This game simulates the management of three Swedish cities (Stockholm, Gothenburg, and Malmö) with a focus on sustainable development. Players make decisions about transportation and energy sources that impact each city's happiness, CO2 emissions, and the overall budget.

## Key Features

- Interactive map of Sweden with city markers
- Turn-based gameplay with decision preview system
- Dynamic news events affecting gameplay
- AI-powered news generation system
- Real-time feedback on city status

## How to Play

1. Start the game server:
```bash
pixi shell
```

2. Launch the application:
```bash
uvicorn main:app --reload
```

3. Open `game_interface.html` in your browser

4. Make decisions for each city and see how they impact the sustainability metrics

## Game Goals

- Keep all cities happy (happiness > 0)
- Minimize CO2 emissions (keep below 100)
- Manage your budget effectively
- Respond to dynamic events that impact your cities

## Technologies Used

- Python FastAPI for backend
- HTML/CSS/JavaScript for frontend
- SVG for map visualization
- AI-powered news generation system
```bash
pixi shell
```
then
```bash
uvicorn main:app --reload
```
then
click the html
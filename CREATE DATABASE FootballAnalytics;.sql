CREATE TABLE epl_player_stats_24_25 (
    ID INT PRIMARY KEY,
    Player_Name VARCHAR(100),
    Club VARCHAR(100),
    Nationality VARCHAR(60),
    Position VARCHAR(10),
    Appearances INT,
    Minutes INT,
    Goals INT,
    Assists INT,
    Shots INT,
    Shots_On_Target INT,
    Conversion_percentage FLOAT,
    Big_Chances_Missed INT,
    Hit_Woodwork INT,
    Offsides INT,
    Touches INT,
    Passes INT,
    Successful_Passes INT,
    Passes_Percentage FLOAT,
    Crosses INT,
    Successful_Crosses INT,
    Crosses_Percentage FLOAT,
    Final_Third_Passes INT,
    Successful_Final_Third_Passes INT,
    Final_Third_Passes_Percentage FLOAT,
    Through_Balls INT,
    Carries INT,
    Progressive_Carries INT,
    Carries_Ended_with_Goal INT,
    Carries_Ended_with_Assist INT,
    Carries_Ended_with_Shot INT,
    Carries_Ended_with_Chance INT,
    Possession_Won INT,
    Dispossessed INT,
    Clean_Sheets INT,
    Clearances INT,
    Interceptions INT,
    Blocks INT,
    Tackles INT,
    Ground_Duels INT,
    Ground_Duels_Won INT,
    gDuels_Percentage FLOAT,
    Aerial_Duels INT,
    Aerial_Duels_Won INT,
    Aerial_Duels_Percentage FLOAT,
    Goals_Conceded INT,
    xG_Threat_Conceded FLOAT,
    Own_Goals INT,
    Fouls INT,
    Yellow_Cards INT,
    Red_Cards INT,
    Saves INT,
    Saves_Percentage FLOAT,
    Penalties_Saved INT,
    Clearances_Off_Line INT,
    Punches INT,
    High_Claims INT,
    Goals_Prevented FLOAT,
    xG FLOAT,
    npxG FLOAT,
    xAG FLOAT,
    Market_Value_In_Millions FLOAT
);

BULK INSERT epl_player_stats_24_25
FROM '/data/epl_player_stats_24_25.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n'
);

SELECT TOP (10) * FROM epl_player_stats_24_25;

--database per90
    CREATE TABLE epl_player_stats_24_25_per90 (
        ID INT PRIMARY KEY,
        Player_Name VARCHAR(100),
        Club VARCHAR(100),
        Nationality VARCHAR(100),
        Position VARCHAR(2),
        Minutes INT,
        -- Goals/Attacking
        Goals_per90 FLOAT,
        Assists_per90 FLOAT,
        Shots_per90 FLOAT,
        Shots_On_Target_per90 FLOAT,
        Conversion_percentage FLOAT,  -- % already normalized
        Big_Chances_Missed_per90 FLOAT,
        Hit_Woodwork_per90 FLOAT,
        Offsides_per90 FLOAT,
        -- Passing
        Touches_per90 FLOAT,
        Passes_per90 FLOAT,
        Successful_Passes_per90 FLOAT,
        Passes_Percentage FLOAT,
        Crosses_per90 FLOAT,
        Successful_Crosses_per90 FLOAT,
        Crosses_Percentage FLOAT,
        Final_Third_Passes_per90 FLOAT,
        Successful_Final_Third_Passes_per90 FLOAT,
        Final_Third_Passes_Percentage FLOAT,
        Through_Balls_per90 FLOAT,
        -- Carrying
        Carries_per90 FLOAT,
        Progressive_Carries_per90 FLOAT,
        Carries_Ended_with_Goal_per90 FLOAT,
        Carries_Ended_with_Assist_per90 FLOAT,
        Carries_Ended_with_Shot_per90 FLOAT,
        Carries_Ended_with_Chance_per90 FLOAT,
        Possession_Won_per90 FLOAT,
        Dispossessed_per90 FLOAT,
        -- Defensive
        Clean_Sheets_per90 FLOAT,
        Clearances_per90 FLOAT,
        Interceptions_per90 FLOAT,
        Blocks_per90 FLOAT,
        Tackles_per90 FLOAT,
        Ground_Duels_per90 FLOAT,
        Ground_Duels_Won_per90 FLOAT,
        Aerial_Duels_per90 FLOAT,
        Aerial_Duels_Won_per90 FLOAT,
        -- GK
        Goals_Conceded_per90 FLOAT,
        Saves_per90 FLOAT,
        Penalties_Saved_per90 FLOAT,
        Punches_per90 FLOAT,
        High_Claims_per90 FLOAT,
        -- Advanced
        xG_per90 FLOAT,
        npxG_per90 FLOAT,
        xAG_per90 FLOAT
        -- % fields & Market_Value μένουν ίδια
    );


INSERT INTO epl_player_stats_24_25_per90 (
    ID, Player_Name, Club, Nationality, Position, Minutes,
    -- Όλα τα per90
    Goals_per90, Assists_per90, Shots_per90, Shots_On_Target_per90,
    Conversion_percentage, Big_Chances_Missed_per90, Hit_Woodwork_per90, Offsides_per90,
    Touches_per90, Passes_per90, Successful_Passes_per90, Passes_Percentage,
    Crosses_per90, Successful_Crosses_per90, Crosses_Percentage,
    Final_Third_Passes_per90, Successful_Final_Third_Passes_per90, Final_Third_Passes_Percentage,
    Through_Balls_per90, Carries_per90, Progressive_Carries_per90, Carries_Ended_with_Goal_per90,
    Carries_Ended_with_Assist_per90, Carries_Ended_with_Shot_per90, Carries_Ended_with_Chance_per90,
    Possession_Won_per90, Dispossessed_per90, Clean_Sheets_per90, Clearances_per90,
    Interceptions_per90, Blocks_per90, Tackles_per90, Ground_Duels_per90, Ground_Duels_Won_per90,
    Aerial_Duels_per90, Aerial_Duels_Won_per90, Goals_Conceded_per90, Saves_per90,
    Penalties_Saved_per90, Punches_per90, High_Claims_per90, xG_per90, npxG_per90, xAG_per90
)
SELECT 
    ID, Player_Name, Club, Nationality, Position, Minutes,
    Goals / NULLIF(Minutes/90.0, 0), Assists / NULLIF(Minutes/90.0, 0),
    Shots / NULLIF(Minutes/90.0, 0), Shots_On_Target / NULLIF(Minutes/90.0, 0),
    Conversion_percentage,
    Big_Chances_Missed / NULLIF(Minutes/90.0, 0), Hit_Woodwork / NULLIF(Minutes/90.0, 0),
    Offsides / NULLIF(Minutes/90.0, 0),
    Touches / NULLIF(Minutes/90.0, 0), Passes / NULLIF(Minutes/90.0, 0),
    Successful_Passes / NULLIF(Minutes/90.0, 0), Passes_Percentage,
    Crosses / NULLIF(Minutes/90.0, 0), Successful_Crosses / NULLIF(Minutes/90.0, 0), Crosses_Percentage,
    Final_Third_Passes / NULLIF(Minutes/90.0, 0), Successful_Final_Third_Passes / NULLIF(Minutes/90.0, 0),
    Final_Third_Passes_Percentage, Through_Balls / NULLIF(Minutes/90.0, 0),
    Carries / NULLIF(Minutes/90.0, 0), Progressive_Carries / NULLIF(Minutes/90.0, 0),
    Carries_Ended_with_Goal / NULLIF(Minutes/90.0, 0), Carries_Ended_with_Assist / NULLIF(Minutes/90.0, 0),
    Carries_Ended_with_Shot / NULLIF(Minutes/90.0, 0), Carries_Ended_with_Chance / NULLIF(Minutes/90.0, 0),
    Possession_Won / NULLIF(Minutes/90.0, 0), Dispossessed / NULLIF(Minutes/90.0, 0),
    Clean_Sheets / NULLIF(Minutes/90.0, 0), Clearances / NULLIF(Minutes/90.0, 0),
    Interceptions / NULLIF(Minutes/90.0, 0), Blocks / NULLIF(Minutes/90.0, 0),
    Tackles / NULLIF(Minutes/90.0, 0), Ground_Duels / NULLIF(Minutes/90.0, 0),
    Ground_Duels_Won / NULLIF(Minutes/90.0, 0), Aerial_Duels / NULLIF(Minutes/90.0, 0),
    Aerial_Duels_Won / NULLIF(Minutes/90.0, 0), Goals_Conceded / NULLIF(Minutes/90.0, 0),
    Saves / NULLIF(Minutes/90.0, 0), Penalties_Saved / NULLIF(Minutes/90.0, 0),
    Punches / NULLIF(Minutes/90.0, 0), High_Claims / NULLIF(Minutes/90.0, 0),
    xG / NULLIF(Minutes/90.0, 0), npxG / NULLIF(Minutes/90.0, 0), xAG / NULLIF(Minutes/90.0, 0)
FROM epl_player_stats_24_25 
WHERE Minutes > 0;


SELECT Position, COUNT(*) as count, AVG(Minutes) as avg_mins 
FROM epl_player_stats_24_25_per90 
GROUP BY Position;
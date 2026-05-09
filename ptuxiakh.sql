USE FootballAnalytics;

BULK INSERT epl_player_stats_24_25
FROM '/data/epl_player_stats_24_25.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n'
);

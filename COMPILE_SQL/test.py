# pylint: disable=no-self-use,missing-function-docstring
"""
Demonstration of the system
"""

class QEnd(Question): # pylint: disable=undefined-variable
    """Question Finale"""
    def question(self):
        return "Tapez du SQL"
    def tester(self):
        self.display('FINI !')
    def default_answer(self):
        return """-- Drop the table because it stays in the browser
DROP TABLE IF EXISTS cities;

-- Create the city population table
CREATE TABLE cities (city string, population number);
INSERT INTO cities VALUES
    ('Paris' ,    10),
    ('Berlin',   100),
    ('Madrid',  1000),
    ('Tokyo' , 10000);

-- Try some SELECT
SELECT * FROM cities WHERE population <= 1000;
SELECT COUNT(*) FROM cities;
SELECT SUM(population) FROM cities;
"""

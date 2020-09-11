import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for Var in self.domains.keys():
            rem =[]
            for Word in self.domains[Var]:
                if Var.length != len(Word):
                    rem.append(Word)
            for Word in rem:
                self.domains[Var].remove(Word)


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.
        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        Overlaps = self.crossword.overlaps[x,y]
        if Overlaps == None:
            return False
        else:
            i = list(Overlaps)[0]
            j = list(Overlaps)[1]
        rem = []
        for Wordx in self.domains[x]:
            #check if any y satisfies constarint of x
            for Wordy in self.domains[y]:
                if Wordx[i] == Wordy[j]:
                    break
            else:
                rem.append(Wordx)
                revised = True
        for Rem in rem:
            self.domains[x].remove(Rem)
        return revised

    def dequeue(self, queue):
        for i,j in queue:
            queue.remove((i,j,))
            return i,j

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.
        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None:
            queue = []
            for i in self.domains.keys():
                for j in self.domains.keys():
                    if i != j:
                        arc = (i,j)
                        queue.append(arc)
        else:
            queue = arcs[::]

        while queue != None:
            (x,y) = self.dequeue(queue)
            if self.revise(x,y):
                if len(self.domains[x]) == 0:
                    return False
                for z in self.crossword.neighbors(x):
                    if z != y:
                        queue.append((z,x,))
            return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for i in self.domains.keys():
            if i not in assignment.keys():
                return False
            else:
                if assignment[i] == None:
                    return False
        return True



    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """

        value = []
        for i,j in assignment.items():
            if j in value:
                return False
            else:
                value.append(j)

            if i.length != len(j):
                return False

            neighbor = self.crossword.neighbors(i)
            for neighb in neighbor:
                Overlaps = self.crossword.overlaps[i,neighb]
                i_corr = list(Overlaps)[0]
                neighb_corr = list(Overlaps)[1]
                if neighb in assignment:
                    if assignment[neighb][neighb_corr] != j[i_corr]:
                        return False

        return True



    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        dict = {}
        value = self.domains[var]
        neighbor = self.crossword.neighbors(var)
        for i in value:
            if i in assignment:
                continue
            else:
                count = 0
                for j in neighbor:
                    if i in self.domains[j]:
                        count += 1
                dict[i] = count
        return sorted(dict, key = lambda k: dict[k])




    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        degree = 0
        value = 1000000
        for i in self.domains.keys():
            if i in assignment:
                continue
            else:
                if value > len(self.domains[i]):
                    variable = i
                    value = len(self.domains[i])
                    if self.crossword.neighbors(i) == None:
                        degree = 0
                    else:
                        degree =  len(self.crossword.neighbors(i))
                elif value == len(self.domains[i]):
                    if self.crossword.neighbors != None:
                        if degree < len(self.crossword.neighbors(i)):
                            variable = i
                            value = len(self.domains[i])
                            degree = len(self.crossword.neighbors(i))
                    else:
                        variable = i
                        value = len(self.domains[i])
                        degree = 0
        return variable


    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.
        `assignment` is a mapping from variables (keys) to words (values).
        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment): return assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var,assignment):
            assignment[var] = value
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result != False: return result
            assignment.pop(var)
        return False



def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()

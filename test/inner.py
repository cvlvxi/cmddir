from typing import List
from dataclasses import dataclass, field


@dataclass
class B:
    item: str

    def update(self, item):
        self.item = item


@dataclass
class A:
    bs: List[B] = field(default_factory=list)


a = A()
a.bs = [B(item="dog"), B(item="cat")]

print(a)

for b in a.bs:
    b.update("horse")


print(a)

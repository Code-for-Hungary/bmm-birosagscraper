from sqlalchemy import ForeignKey, Column
from sqlalchemy import String, Integer, Table
from sqlalchemy.orm import DeclarativeBase

from sql_stuff.database import engine


# METADATA
# Main
# - Határozat sorszáma (B.27/2022/40)
# - Bíróság (Miskolci Törvényszék)
# - Kollégium (büntető)
# - Jogterület (büntetőjog)
# - Év (2022)
# Detail
# - Egyedi azonositó (5-BJ-2022-11)
# - Kapcsolódó határozatok (Debreceni Ítélőtábla Bf.621/2022/7 ; )
# - Jogszabályhelyek (2012. évi C. törvény a Büntető Törvénykönyvről 37. § (3) - 2020-08-14; \n...)
# - A határozat elvi tartalma (kábítószer-kereskedelem, új pszichoaktív anyaggal visszaélés)
# Additional
# - URL /anonimizalt-hatarozatok?azonosito=Bf.621/2022/7&birosag=Debreceni Ítélőtábla


class Base(DeclarativeBase):
    pass


kapcsolodo_hatarozatok_table = Table(
    'kapcsolodo_hatarozatok',
    Base.metadata,
    Column('id-1', Integer, ForeignKey('hatarozat.id'), index=True),
    Column('id-2', Integer, ForeignKey('hatarozat.id'), index=True)
)


class Hatarozat(Base):
    __tablename__ = "hatarozat"
    id = Column(Integer, primary_key=True)

    # Main columns
    sorszam = Column(String(250), unique=True, index=True, nullable=False)
    birosag = Column(String(250), nullable=False)
    kollegium = Column(String(250), nullable=False)
    jogterulet = Column(String(250), nullable=False)
    year = Column(Integer, index=True, nullable=False)

    # Details
    egyedi_azonosito = Column(String(250), unique=True, index=True, nullable=False)
    jogszabalyhelyek = Column(String)
    elvi_tartalma = Column(String)

    # Additional
    url = Column(String)
    filepath = Column(String)

    # Text of hatarozat
    hatarozat_text = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"Hatarozat(id={self.id!r}, sorszam={self.sorszam!r}, year={self.year!r})"

Base.metadata.create_all(engine)

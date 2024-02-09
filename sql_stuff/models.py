from sqlalchemy import ForeignKey, Column
from sqlalchemy import String, Integer, Table
from sqlalchemy.orm import DeclarativeBase


from database import Session, engine


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


kapcsolodo_hatarozatok = Table(
    'kapcsolodo_hatarozatok',
    Base.metadata,
    Column('id-1', Integer, ForeignKey('hatarozat.id'), index=True),
    Column('id-2', Integer, ForeignKey('hatarozat.id'), index=True)
)

kapcsolodo_elvi_tartalmak = Table(
    'kapcsolodo_elvi_tartalmak',
    Base.metadata,
    Column('elvi_tartalom_id', Integer, ForeignKey('elvi_tartalom.id'), index=True),
    Column('hatarozat_id', Integer, ForeignKey('elvi_tartalom.id'), index=True)
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
    # kapcsolodo_hatarozatok
    jogszabalyhelyek = Column(String)
    elvi_tartalma = Column(ForeignKey('elvi_tartalom.id'))
    # Additional
    url = Column(String)

    def __repr__(self) -> str:
        return f"Hatarozat(id={self.id!r}, sorszam={self.sorszam!r}, year={self.year!r})"


class ElviTartalom(Base):
    __tablename__ = "elvi_tartalom"
    id = Column(Integer, primary_key=True)
    tartalom_elnevezes = Column(String)

    def __repr__(self) -> str:
        return f"ElviTartalom(id={self.id!r}, tartalom_elnevezes={self.tartalom_elnevezes!r})"


Base.metadata.create_all(engine)

